"""Decision Tree Creation Frontend for Athlete Date."""


import requests
import json
from dash import Dash, dash_table, dcc, html, callback, Output, Input, State, \
    callback_context
import pandas as pd
import dash_cytoscape as cyto
from psycopg2 import connect

# Required for the hierarchical network
cyto.load_extra_layouts()
# Tracking the node number
counter = 0
# Database
conn = connect(
    dbname="postgres",
    user="postgres",
    host="localhost",
    password="postgres")

# if a internet connection exits
try:
    url = 'https://inprove-sport.info/csv/getInproveDemo/hgnxjgTyrkCvdR'
    # Get website data
    response = requests.get(url)
    data_raw = response.json()
# no internet connection
except:
    # Not possible to download data -> use existing text file
    with open('data.txt', 'r') as f:
        data_raw = json.loads(f.read())

# Load data into a DataFrame
data = pd.json_normalize(data_raw, record_path=['res'])
data['testID'] = data['testID'].astype(str)
table = data.pivot_table(index="athleteID", columns="testID",
                         values="testValue")
# Create an additional column with the athleteID (the index of the table row)
# -> columns now contain all testIDs and the AthleteID
table["athID"] = table.index
# Create list with all athleteIDs
athlete_names = table['athID'].to_list()

# At the beginning there is only root node (label contains all athletes)
# = [{'data': {'id': 'everybody', 'label': '[1000, 1027, ...]'}}]
nodes = [{'data': {'id': 'everybody', 'label': str(athlete_names)}}]
edges = []
recommendations = {}

# Stylesheet for the network
network_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'background-color': 'lightgrey',
            'font-size': 12,
            # place text in the middle
            'text-valign': 'center',
            'text-halign': 'center',
            # Label is the text that will be displayed in the nodes
            # By data(id) I select the id of the node as text
            # At the beginning this is everybody
            'label': 'data(id)'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': 'yellow',
            # In the label of the edges I store the applied threshold
            'label': 'data(label)',
            'font-size': 9
        }
    }
]


# Define style for testID buttons
def testID_buttons_style():
    return {
        'font-size': 20,
        'width': '50px',
        'height': '50px',
        'margin': '12px',
        "padding": "13px",
        'border-radius': "50%",
        'background-color': 'orange'
    }


# Initialize the app
app = Dash(__name__, title="Decision Tree Creation Athletes",
           prevent_initial_callbacks=True, suppress_callback_exceptions=True)

app.layout = html.Div([

    html.H1("Decision Tree Creation Athletes"),

    dash_table.DataTable(
        # Expects list of dicts.
        # From each row of my PivotTable (i.e. each athlete) a separate
        # dictionary is created with the testIDs as keys
        data=table.to_dict('records'),
        # The i in the columns (testID) is used both as column header and id
        columns=[{'name': i, 'id': i} for i in table.columns],
        page_size=5,
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

    # Div contains Threshold-Menu, Note-selection-Menu, Node-Buttons on the
    # left side, Recommendations in the middle and save-tree button on the
    # right
    html.Div([
        # Store Threshold-Menu, Note-Dropdown-Menu, Node-Buttons
        html.Div
            (children=[

            # User input Threshold
            html.Label("Threshold: "),
            dcc.Input(id='threshold', type='number', min=1, max=10, value=5),

            html.Br(),
            html.Br(),

            html.Label("Please select a node: "),
            # Node-Dropdown menu
            # takes options (a list with all elements the menu contains)
            # and value (displayed (default) element) as input
            html.Div(
                children=[dcc.Dropdown(id="nodes-dropdown", clearable=False)],
                style={'width': 400}),

            # Creates buttons for each column index (testID) of the table
            # Omit the column with athleteID
            # The id of each button is: "str(i)" !
            html.Div(
                children=[
                    html.Button(style=testID_buttons_style(), children=f"{i}",
                                id=str(i)) for i in table.columns if
                    i != 'athID'], style={'align-items': 'center'}
            ),

            html.Br(),

            # instructions
            html.Div("1. Enter a valid Threshold"),
            html.Br(),
            html.Div("2. Select a node"),
            html.Br(),
            html.Div("3. Choose a Test ID"),

        ],
            style={'width': '45%', 'display': 'inline-block'}),

        # Write/store Recommendations
        html.Div(children=[

            html.Button('Save Recommendations', id='save-recommendation'),

            html.Br(),

            dcc.Textarea(
                id='recommendation',
                value='',
                style={'width': 400, 'height': 100},
            ),

            # Show when recommendation is saved
            html.Div(id='text-saved', children=""),
            html.Br(),
            html.Br(),

            # If there are problems updating the elements (tree),
            # the error is displayed here
            html.Div(id='network-issues', children=""),

        ],

            style={'width': '30%', 'display': 'inline-block',
                   'vertical-align': 'top'}),

        # Save the tree in a postgres table
        html.Div(children=[

            html.Button('Save Tree', id='save-tree'),
            html.Br(),
            dcc.Input(
                id='tree-id',
                type="text"
            ),
            # Show when tree is stored or if id already exists
            html.Div(id='stored', children="")

        ],

            style={'width': '25%', 'display': 'inline-block',
                   'float': 'right'}),

    ]),

    # Display the node description that was selected
    html.Div(id='node-description-output'),

    html.Br(),

    # Network
    cyto.Cytoscape(
        id='network',
        # Node format: {'data': {'id': 'Node_id', 'label': 'node_label'}
        # Edge format: {'data': {'source': 'start node', 'target': 'end node',
        # 'label': 'edge_label'}}
        # At beginning:
        # nodes = [{'data': {'id': 'everybody', 'label': '[1000, 1027, ...]'}}]
        #       only root node
        # edges = []
        elements=edges + nodes,
        style={'width': '100%', 'height': '500px'},
        layout={'name': 'dagre', 'animate': True},  # 'locked'=True
        stylesheet=network_stylesheet
    )])


@callback(Output('network', 'elements'),
          Output('network-issues', 'children'),
          # str(i) is the button id
          [Input(str(i), "n_clicks") for i in table.columns if i != 'athID'],
          State('network', 'elements'),
          State('threshold', 'value'),
          State("nodes-dropdown", "value"))
def update_elements(*args):
    """Functions updates the nodes + edges.
    Called when one of the testID buttons is pressed.
    Input:
        The (testID) Buttons,
        The current state of the network elements, the threshold value and the
        leaf node on which the threshold is applied (nodes-dropdown value).
    args is used so the number of testIDs is flexible.

    """
    global counter
    global recommendations
    # Get the testID
    cur_testID = callback_context.triggered[0]["prop_id"].split(".")[0]
    # buttons (so all table columns) are part of the input so the elements are
    # at index len(table.columns) - 1
    elements = args[len(table.columns) - 1]
    # Get all nodes from elements
    # remember: node has 'id' and edge has 'source' and 'target'
    nodes = [item for item in elements if next(iter(item['data'])) == "id"]
    edges = [item for item in elements if next(iter(item['data'])) == "source"]
    threshold = args[len(table.columns)]
    # If no or no valid threshold is selected. For numbers outside the
    # limits (1,10) the threshold value is automatically None
    if threshold is None:
        return nodes + edges, "PLEASE SELECT A VALID THRESHOLD FROM 1 TO 10"
    if cur_testID != '':
        # leaf_node is the node to which the threshold is applied.
        # It is the node selected in the dropdown menu
        leaf_node = str(args[len(table.columns) + 1])
        # At the label position of each node I always store all contained
        # athletes. Now I want to get all athlete that my leaf_node contains
        athletes = \
            [item for item in nodes if item["data"]["id"] == leaf_node][0][
                "data"][
                "label"]
        # when there are no athletes then it does not go further
        if len(athletes) <= 2:
            return nodes + edges, "NODE CONTAINS NO ATHLETES"
        # if the frontend gets reloaded
        if leaf_node == "everybody":
            # set counter to 1 and empty recommendations.
            counter = 1
            recommendations = {}
        else:
            counter += 1
        # Select only the athletes the leaf node contains in the table
        df_ath = table.loc[json.loads(athletes)]
        # Only the relevant TestID
        df_ath = (df_ath[cur_testID])
        # Get and add the new nodes and edges
        nodes1, edges1 = data_split(df_ath, cur_testID, threshold, leaf_node,
                                    counter)
        edges.extend(edges1)
        nodes.extend(nodes1)
    # Return the (new) elements to the network (no error message needed)
    return nodes + edges, ""


def data_split(df_ath, testID, threshold, leaf_node, cur_counter):
    """Function splits the athletes in two nodes"""
    # Create two tables for the correct athletes.
    athl_left = df_ath[df_ath <= threshold]
    athl_right = df_ath[df_ath > threshold]
    """
    remember:
    node = {'data': {'id': 'one', 'label': 'Node 1'}}
    edge =  {'data': {'source': 'one', 'target': 'two', 'label': 'Node 1'}}] 
    """

    # Create 2 new nodes. id of the left one is "node{cur_counter}-l" and of
    # the right one "node{cur_counter}-r". In the label the respective
    # athletes which the node contains are written
    nodes = [{'data': {'id': my_id, 'label': my_label}} for my_id, my_label in
             ((f"node{cur_counter}-l", str(athl_left.index.tolist())),
              (f"node{cur_counter}-r", str(athl_right.index.tolist())))]

    # Create 2 new edges from the leaf_node (source) to the two new nodes.
    # As label of the edge the applied threshold is stored.
    # To the left node this is: "{testID}<={threshold}".
    # Remember: The Threshold label is displayed in the network Stylesheet as
    # Edge label
    edges = [{'data': {'source': source, 'target': target, 'label': label}} for
             source, target, label in
             ((leaf_node, f"node{cur_counter}-l", f"{testID}<={threshold}"),
              (leaf_node, f"node{cur_counter}-r", f"{testID}>{threshold}"))]
    return nodes, edges


@callback(Output("nodes-dropdown", "options"),
          Output("nodes-dropdown", "value"),
          Input('network', 'elements')
          )
def update_dropdown_menu(elements):
    """Updates the leave nodes in nodes-dropdown-menu.
    If any of the elements (nodes + edges) in the network is changed (so always
    after update_elements was called), then update_dropdown_menu is called
    with the new elements as input.
    The dropdown menu (in which the nodes are selected to which the
    threshold is applied) will then be adjusted so that only the leaf nodes
    are displayed there.

    """
    nodes = [item for item in elements if next(iter(item['data'])) == "id"]
    # If there is only the root node (at the beginning)
    if len(nodes) == 1:
        return [nodes[0]['data']['id']], nodes[0]['data']['id']
    # Get all edges from elements
    edges = [item for item in elements if next(iter(item['data'])) == "source"]
    # Store the nodes which are available for the next threshold selection
    end_nodes = []
    # All nodes that are the starting point of an edge
    node_ids = {n['data']['source'] for n in edges}
    for n in nodes:
        # All nodes that are not the starting point of an edge -> These nodes
        # are leaves -> A threshold can be applied to them
        if n['data']['id'] not in node_ids:
            # store the id of these nodes
            end_nodes.append(n['data']['id'])
    # Value is the default node that is displayed in the dropdown menu
    value = end_nodes[0]
    # Return to nodes-dropdown-menu
    return end_nodes, value


@callback(Output('node-description-output', 'children'),
          Input('network', 'tapNodeData'))
def displayTapNodeData(data):
    """Shows All Athletes of the network node.
    When a node in the network is pressed, displayTapNodeData  and all athletes
    of the node are displayed in the node-description-output element.

    """
    if data:
        # data['label'] stores all athletes of this node
        return "Node description of " + data['id'] + ": " + data['label']


# allow_duplicate -> multiple callback functions address the same div.
@callback(Output('text-saved', 'children', allow_duplicate=True),
          Input('save-recommendation', 'n_clicks'),
          State('recommendation', 'value'),
          State("nodes-dropdown", "value"),
          prevent_initial_call=True)
def update_recommendation(num_clicks, cur_rec, tree_id):
    """Store text of selected leaf node.
    Is called when save-text is clicked.
    Takes the current state of the text and the current node in the dropdown
    menu as input.
    Stores the text for current leaf-node in the dropdown menu.
    Caution. The text applies to the node that is currently selected in the
    dropdown menu and not the node for which is currently displayed in the
    node description. Since only the leaves are displayed in the dropdown menu,
    the recommendation can only be stored/displayed for them.

    """
    # If a node in the dropdown menu is selected
    if tree_id is not None:
        # Store the text for the node in the dictionary
        recommendations[tree_id] = cur_rec
        # Show the user for which node the recommendation is saved
        return tree_id + " stored"
    # Callback function has to have a return. Return "" if not recommendation
    # is saved
    return ''


@callback(Output("recommendation", "value"),
          Output("text-saved", "children", allow_duplicate=True),
          Input("nodes-dropdown", "value"),
          prevent_initial_call=True)
def load_recommendation(tree_id):
    """Show recommendation of selected node in dropdown menu"""
    try:
        text = recommendations[tree_id]
    except:
        text = ''
    # return recommendation of node
    # per default no text is shown in the text-saved field. Only if a new
    # recommendation is stored it is shown there
    return text, ""


@callback(Output('stored', 'children'),
          Input('save-tree', 'n_clicks'),
          State('network', 'elements'),
          State('tree-id', 'value'))
def store_results(num_clicks, elements, tree_id):
    """Stores the trees (nodes + edges) + recommendations in the database."""
    # If an id is entered
    if tree_id is not None:
        try:
            # create connection
            cursor = conn.cursor()
            # test with dummy select whether the connection works
            cursor.excecute("select tree_id from store limit 1")
        except:
            conn = connect(dbname="postgres", user="postgres",
                           host="localhost", password="postgres")
            cursor = conn.cursor()
        # create query with placeholders
        query = '''INSERT INTO store VALUES (%s,%s, %s)'''
        try:
            # Try to execute the sql query.
            # Store treeID, elements, recommendations in table "store"
            # Convert Tree elements (nodes + edges) and recommendations to JSON
            # objects
            # Tree ID is stored in first col: tree_id (character)
            # Elements are stored in second col: elements (json)
            # Recommendations are stored in third col: recommendations (json)
            cursor.execute(query, (
                tree_id, json.dumps(elements), json.dumps(recommendations)))
            conn.commit()
            cursor.close()
        except:
            return "ID exists already"
        # Show user that tree is saved
        return tree_id + " stored"

    else:
        return 'Please enter an id'


# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8077)
