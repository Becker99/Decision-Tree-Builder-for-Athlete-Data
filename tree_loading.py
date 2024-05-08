"""Decision Tree Loading Frontend for Athlete Date."""


import json
import dash_cytoscape as cyto
import pandas as pd
import requests
from dash import Dash, dash_table, dcc, html, callback, Output, Input, State
from dash.exceptions import PreventUpdate
from psycopg2 import connect

recommendations = {}

# Database
conn = connect(
    dbname="postgres",
    user="postgres",
    host="localhost",
    password="postgres")

cyto.load_extra_layouts()

try:
    url = 'https://inprove-sport.info/csv/getInproveDemo/hgnxjgTyrkCvdR'
    response = requests.get(url)
    data_raw = response.json()
except:
    # Not possible to download data -> use existing text file
    with open('data.txt', 'r') as f:
        data_raw = json.loads(f.read())

data = pd.json_normalize(data_raw, record_path=['res'])
data['testID'] = data['testID'].astype(str)
table = data.pivot_table(index="athleteID", columns="testID",
                         values="testValue")
table["athID"] = table.index

# Stylesheet for the network
network_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'background-color': 'lightgrey',
            'font-size': 12,
            'text-valign': 'center',
            'text-halign': 'center',
            'label': 'data(id)'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': 'yellow',
            'label': 'data(label)',
            'font-size': 9
        }
    }
]

# Initialize the app
app = Dash(__name__, title="Decision Tree Loading",
           prevent_initial_callbacks=True,
           suppress_callback_exceptions=True)

app.layout = html.Div([

    html.H1("Decision Tree Loading"),

    # Show athlete Data
    dash_table.DataTable(
        data=table.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in table.columns],
        page_size=5,
        # Select one row at a time
        row_selectable='single',
        # Cells are editable -> allows to enter new values for athlete data
        editable=True,
        # Filter data directly in the table by entering expression in col
        # bsp: "> 5" -> select only the athletes (rows) with "testID > 5"
        filter_action='native',
        id='data',
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
        },
        style_data={
            'backgroundColor': 'grey',
            'color': 'white'
        },
    ),

    html.Label("Please select a Tree: "),
    # Contains all stored Trees. Updates once at the beginning.
    html.Div(children=[dcc.Dropdown(id="tree-dropdown", clearable=False)],
             style={'width': 400}),

    # Is needed for callback -- to load all stored trees at the beginning.
    # Every callback needs an input. Is hidden
    html.Div(children=[dcc.Input(id='nothing', type='number')],
             style={'visibility': 'hidden'}),

    # Load and display the Tree
    html.Button('Load Tree', id='load-tree'),
    html.Br(),
    html.Br(),

    # Click to display the recommendation for the selected row of the table
    html.Button('Display Recommendation', id='disp-recom'),

    html.Br(),

    # Network
    html.Div([
        html.Div(children=[

            cyto.Cytoscape(
                id='network',
                elements=[],
                style={'width': '100%', 'height': '500px'},
                layout={'name': 'dagre', 'animate': True},
                stylesheet=network_stylesheet
            ),
        ], style={'width': '75%', 'display': 'inline-block'}),

        # Display recommendation
        html.Div(children=[
            # Show which tree node is reached by the selected athlete row
            html.Div(id="node", children=''),
            html.Br(),
            # show the recommendation
            dcc.Textarea(
                id='recommendation',
                value='',
                style={'width': 400, 'height': 100},
            ),
        ], style={'width': '25%', 'display': 'inline-block',
                  'vertical-align': 'top'}),
    ])
])


@callback(Output('tree-dropdown', 'options'),
          Output('tree-dropdown', 'value'),
          State('tree-dropdown', 'value'),
          Input('nothing', 'value'))
def update_dropdown(tree, x):
    """Displays all available trees in the dropdown menu.
    Function is called once at the beginning.
    """
    # input should be (None, None)
    if x is None and tree is None:
        # Declare a cursor object from the connection
        # Cursor allows me to execute sql statements
        cursor = conn.cursor()
        # select all tree_ids (first col.)
        cursor.execute('''select tree_id from store''')
        # rows =  [('tree1     ',), ('tree2     ',)]
        # print(rows)
        tmp = cursor.fetchall()
        ids = []
        for y in tmp:
            ids.append(y[0])
        ids.sort()
        cursor.close()
        # return all ids + the first id as default to tree dropdown menu
        return ids, ids[0]
    else:
        raise PreventUpdate


@callback(Output('network', 'elements'),
          Output('recommendation', 'value', allow_duplicate=True),
          Output("node", "children", allow_duplicate=True),
          Input('load-tree', 'n_clicks'),
          State('tree-dropdown', 'value'),
          prevent_initial_call=True)
def load_network(num_clicks, cur_tree):
    """Display the selected Tree and store his recommendations """
    global recommendations
    # so it does not load at the beginning
    if num_clicks is not None:
        cursor = conn.cursor()
        # Get all the data (nodes + keys and recommendations) from the tree
        # stored in the database store. Select the tree id chosen in the
        # dropdown menu.
        query = '''select * from public.store where tree_id = %(tree)s;'''
        cursor.execute(query, {'tree': cur_tree})
        row = cursor.fetchone()
        # print(row)
        # ('tree1     ', [{'data': {'id': 'everybody', ...}},...],
        # {'node1-l': 'node1-l test', 'node1-r': 'node1-r test'})
        # update recommendations
        recommendations = row[2]
        # return elements [nodes+edges] to network
        # every time a new tree is shown the recommendation gets set to ""
        return row[1], "", ""
    # at the beginning -> return empty network elements (no tree)
    return [], "", ""


@callback(Output('recommendation', 'value', allow_duplicate=True),
          Output("node", "children", allow_duplicate=True),
          Input('disp-recom', 'n_clicks'),
          State('data', 'derived_virtual_selected_rows'),
          State('data', 'derived_virtual_data'),
          State('network', 'elements'),
          prevent_initial_call=True)
def row_action(num_clicks, index_list, data, elements):
    """Display recommendation for the selected athlete-row.
    Function gets called when the Display Recommendation button is clicked.

    Store all edges. Store for my athlete for every edge if the condition is
    fulfilled (True) or not (False).
    Store for every edge that is True the source and target node in dict.
    Go through the dict and start at the first node (everybody) and see to
    which target node it leads us. Then take this target node and see where it
    leads us and so on until we have a node from which no edge is coming out.
    """
    # If the button is clicked, a row is selected and a tree is selected
    if num_clicks is not None and index_list is not None and data is not None:
        try:
            # Get the data of the right athlete
            athlete_row = (data[index_list[0]])
            # Get all edges
            edges = [item for item in elements if
                     next(iter(item['data'])) == "source"]
            # Get all thresholds
            # = [edge["data"]["label"] for edge in edges]
            labels = [edges[i]["data"]["label"] for i in range(len(edges))]
            # threshold[:3] = <testID>
            # athlete[threshold[:3]] is the value of the athlete at this testID
            # threshold[3:] is the criteria z.B. <=5
            # athlete[threshold[:3]] +  threshold[3:] =  ['9<=5', '9>5']
            # -> shows for each edge if its fulfilled
            newlabels = [str(athlete_row[threshold[:3]]) + threshold[3:] for
                         threshold in labels]
            # Store for every edge if the Threshold is True or False
            # [False, True] -> follow second edge
            # order is the same as in edges
            eval_newlabels = [eval(item) for item in newlabels]
            # dict with all source and target node res[source_1] = target_1
            res = {}
            for i in range(len(edges)):
                # if the threshold comparison for this athlete is True
                # -> store source and target node for every fulfilled threshold
                if eval_newlabels[i] == True:
                    res[edges[i]["data"]["source"]] = edges[i]["data"][
                        "target"]
            # everybody is start node for every tree
            # -> is always the first source node (if tree as only the root it's
            # the end node)
            current_node = "everybody"
            # follow the fulfilled edges.
            # res[everybody] = first_target -> res[first_target] =
            # second_target ... res[target_n-1] = end_node
            while current_node in res:
                current_node = res[current_node]
            # get recommendation if one is stored in the table
            try:
                recommend = recommendations[current_node]
            # if no recommendation is stored for this node
            except:
                recommend = ''
            return recommend, "Recommendation Node: " + \
                              current_node
        except:
            return "", ""
    else:
        raise PreventUpdate


# Run the app, port 8050 so that there is no overlap with the other app
if __name__ == '__main__':
    app.run(debug=True, port=8050)
