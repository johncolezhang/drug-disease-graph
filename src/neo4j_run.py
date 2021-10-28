#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from util.neo4j_util import neo4jUtil
import json

def step4_upload_neo4j():
    neo4j_host = "neo4j://172.16.229.46:7687"
    neo4j_user = "neo4j"
    neo4j_pwd = "123456"
    neo4j_database = "neo4j"

    neo_util = neo4jUtil(host=neo4j_host, user=neo4j_user, password=neo4j_pwd)

    node_filepath = "json/nodes.json"
    edge_filepath = "json/edges.json"

    # node_list = ["drug", "disease", "symptom"]
    # for nl in node_list:
    #     print("Delete node: {}".format(nl))
    #     neo_util.delete_node_by_label(neo4j_database, nl)

    print("Add nodes")
    with open(node_filepath) as f:
        node_list = json.load(f)
    neo_util.add_node_to_neo4j(node_list, neo4j_database)

    # print("Add edges")
    # with open(edge_filepath) as f:
    #     edge_list = json.load(f)
    # neo_util.add_edge_to_neo4j(edge_list, neo4j_database)


if __name__ == "__main__":
    step4_upload_neo4j()
