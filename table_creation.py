"""Create Table for Tree storage"""


# psycopg2 is a Python adapter for PostgreSQL database
# import connect to create a connection to my PostgreSQL database
from psycopg2 import connect

conn = connect(
    dbname="postgres",
    user="postgres",
    host="localhost",
    password="postgres")

# Declare a cursor object from the connection
# Cursor allows me to execute sql statements
cursor = conn.cursor()


"""
Create table with name Store if it does not already exist.
Contains three columns:
    "treeID" type "character(10)" -> My Primary Key. Stores Tree ID 
    "elements" type "json
    "recommendations" type "json
TABLESPACE pg_default; -> Table is stored in default tablespace


"""
query = '''
CREATE TABLE IF NOT EXISTS public.store 
(
    tree_id character(10) COLLATE pg_catalog."default" NOT NULL,
    elements json,
    recommendations json,
    CONSTRAINT store_pkey PRIMARY KEY (tree_id)
)
TABLESPACE pg_default;

'''

cursor.execute(query)
conn.commit()
# Close cursor object to avoid memory leaks
cursor.close()
# Close the connection
conn.close()
