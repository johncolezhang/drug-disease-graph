#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from util.neo4j_util import neo4jUtil
import json

def step4_upload_neo4j():
    neo4j_host = "neo4j://172.16.231.80:7687"
    neo4j_user = "neo4j"
    neo4j_pwd = "123456"
    neo4j_database = "neo4j"
    neo_util = neo4jUtil(host=neo4j_host, user=neo4j_user, password=neo4j_pwd)

    """
    #####################################################
    print("delete node by label")
    node_list = ["drug", "disease", "symptom"]
    for nl in node_list:
        print("Delete node: {}".format(nl))
        neo_util.delete_node_by_label(neo4j_database, nl)

    print("Add nodes")
    with open("json/nodes.json", "r") as f:
        node_list = json.load(f)
    neo_util.add_node_to_neo4j(node_list, neo4j_database)

    print("Add edges")
    with open("json/edges.json", "r") as f:
        edge_list = json.load(f)
    neo_util.add_edge_to_neo4j(edge_list, neo4j_database)
    #######################################################

    #######################################################
    print("delete edge by label")
    edge_list = ["chemical_drug_relation", "drug_interaction"]
    for el in edge_list:
        neo_util.delete_node_by_label(neo4j_database, el)

    with open("json/dc_nodes.json", "r") as f:
        node_list = json.load(f)
    neo_util.add_node_to_neo4j(node_list, neo4j_database)

    with open("json/dc_edges.json", "r") as f:
        edge_list = json.load(f)
    neo_util.add_edge_to_neo4j(edge_list, neo4j_database)

    # data from drug interaction is incorrect
    # with open("json/drug_interact_nodes.json", "r") as f:
    #     node_list = json.load(f)
    # neo_util.add_node_to_neo4j(node_list, neo4j_database)
    #
    # with open("json/drug_interact_edges.json", "r") as f:
    #     edge_list = json.load(f)
    # neo_util.add_edge_to_neo4j(edge_list, neo4j_database)
    ########################################################
    """

    ########################################################
    with open("json/all_drug_nodes.json", "r") as f:
        node_list = json.load(f)
    neo_util.add_node_to_neo4j(node_list, neo4j_database)
    ########################################################

    ########################################################
    with open("json/all_disease_nodes.json", "r") as f:
        node_list = json.load(f)
    neo_util.add_node_to_neo4j(node_list, neo4j_database)
    ########################################################

    """
    ########################################################
    # relation match by Chinese
    with open("json/new_che_drug_edges.json", "r") as f:
        edge_list = json.load(f)
    neo_util.add_edge_to_neo4j(edge_list, neo4j_database)
    ########################################################

    ########################################################
    # cn drug label
    with open("json/cn_dl_nodes.json", "r") as f:
        node_list = json.load(f)
    neo_util.add_node_to_neo4j(node_list, neo4j_database)

    with open("json/cn_dl_edges.json", "r") as f:
        edge_list = json.load(f)
    neo_util.add_edge_to_neo4j(edge_list, neo4j_database)
    ########################################################
    """
    ########################################################
    # # generate disease degree
    # with open("json/disease_degree_nodes.json", "r") as f:
    #     node_list = json.load(f)
    # neo_util.add_node_to_neo4j(node_list, neo4j_database)
    #########################################################


    #########################################################
    # # generate new drug disease relation
    # with open("json/new_drug_disease_edges.json", "r") as f:
    #     edge_list = json.load(f)
    # neo_util.add_edge_to_neo4j(edge_list, neo4j_database)
    ##########################################################

if __name__ == "__main__":
    step4_upload_neo4j()
