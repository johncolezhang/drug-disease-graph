#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from py2neo import Graph
import pandas as pd
import json

session = Graph("neo4j://172.16.231.80:7687", auth=("neo4j", "123456"))

cypher_template = """
MATCH (n:disease)
WITH n, size((n)<-[:treatment]-()) as degree
return n.disease_name as disease_name, degree order by degree desc
"""

degree_list = session.run(cypher_template).data()
df_degree = pd.DataFrame(degree_list)

df_degree = df_degree[df_degree["disease_name"].str.len() >= 2]

cypher_template = """
MATCH (n:disease) return n.disease_name as disease_name
"""

dis_list = session.run(cypher_template).data()
df_dis = pd.DataFrame(dis_list)

df_merge = pd.merge(df_dis, df_degree, how="left", on=["disease_name"])
df_merge = df_merge.fillna(0)

# df_merge.to_csv("processed/disease_degree.csv", index=False)

node_list = []
for index, row in df_merge.iterrows():
    if row["disease_name"] != "":
        dis_node = {
            "label": ["disease"],
            "node_ID": "disease_name",
            "property": {
                "disease_name": row["disease_name"],
                "display": row["disease_name"],
                "disease_degree": int(row["degree"])
            }
        }
        node_list.append(dis_node)

with open("json/disease_degree_nodes.json", "w") as f:
    json.dump(node_list, f)
