#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from neo4j import GraphDatabase

class neo4jUtil:
    def __init__(self, host, user, password):
        self.driver = GraphDatabase.driver(
            host,
            auth=(user, password)
        )

    @staticmethod
    def neo4j_run_cypher(tx, cypher_statement):
        tx.run(cypher_statement)

    @staticmethod
    def gen_add_node_cypher(node_info):
        # add new node
        # check node_ID, if node exists, merge all properties.
        node_ID = node_info['node_ID']
        label_list = node_info['label']
        property_dict = node_info['property']
        node_ID_value = ""
        if node_ID in property_dict.keys():
            node_ID_value = property_dict[node_ID]
        cypher_statement = 'MERGE (n'
        for label in label_list:
            cypher_statement = cypher_statement + ":" + label
        cypher_statement = cypher_statement + " {" + node_ID + ":\"" + str(node_ID_value) + "\"})" + "\n"
        cypher_statement = cypher_statement + "SET n += {"
        # add node property
        for key in property_dict.keys():
            property_value = property_dict[key]
            # if property_value == "":
            #     continue
            cypher_statement = cypher_statement + key + ":\"" + str(property_value) + "\", "
        cypher_statement = cypher_statement[:-2]
        cypher_statement = cypher_statement + "}\n"
        return cypher_statement

    @staticmethod
    def gen_add_edge_cypher(edge_info):
        start_node = edge_info['start_node']
        end_node = edge_info['end_node']
        edge = edge_info['edge']
        cypher_statement = "MATCH (s"
        # match node
        if "label" in start_node.keys():
            label = start_node["label"]
            if type(label) == list:
                label = ":".join(label)
            cypher_statement = cypher_statement + ":" + label
        cypher_statement = cypher_statement + "), (e"
        if "label" in end_node.keys():
            label = end_node["label"]
            if type(label) == list:
                label = ":".join(label)
            cypher_statement = cypher_statement + ":" + label
        cypher_statement = cypher_statement + ")\nWHERE"
        start_node_property = start_node['property']
        for key in start_node_property.keys():
            value = str(start_node_property[key])
            if value == "":
                continue
            cypher_statement = cypher_statement + "\ns." + key + " = \"" + str(value) + "\" AND"
        end_node_property = end_node['property']
        for key in end_node_property.keys():
            value = str(end_node_property[key])
            if value == "":
                continue
            cypher_statement = cypher_statement + "\ne." + key + " = \"" + str(value) + "\" AND"
        cypher_statement = cypher_statement[:-3] + "\nMERGE\n(s) -[r:"
        edge_label = edge["label"]
        cypher_statement = cypher_statement + edge_label
        # add property for edge
        if "property" in edge.keys():
            edge_property = edge["property"]
            if len(edge_property) > 0:
                cypher_statement = cypher_statement + " {"
                for key in edge_property.keys():
                    value = str(edge_property[key])
                    # if value == "":
                    #     continue
                    cypher_statement = cypher_statement + key + ":\"" + value + "\","
                cypher_statement = cypher_statement[:-1] + "}"
        cypher_statement = cypher_statement + "]-> (e)"
        return cypher_statement

    def add_node_to_neo4j(self, node_list, database):
        with self.driver.session(database=database) as session:
            for node_info in node_list:
                try:
                    cypher_statement = self.gen_add_node_cypher(node_info)
                    session.write_transaction(self.neo4j_run_cypher, cypher_statement)
                except Exception as e:
                    continue

    def add_edge_to_neo4j(self, edge_list, database):
        with self.driver.session(database=database) as session:
            for i in range(0, len(edge_list)):
                edge_info = edge_list[i]
                cypher_statement = self.gen_add_edge_cypher(edge_info)
                if len(cypher_statement.strip()) > 0:
                    session.write_transaction(self.neo4j_run_cypher, cypher_statement)

    def delete_all_neo4j(self, database):
        with self.driver.session(database=database) as session:
            cypher_statement = "match (n) detach delete n"
            session.write_transaction(self.neo4j_run_cypher, cypher_statement)

    def delete_node_by_label(self, database, label):
        with self.driver.session(database=database) as session:
            cypher_statement = "match (n: {}) detach delete n".format(label)
            session.write_transaction(self.neo4j_run_cypher, cypher_statement)

    def delete_relation_by_label(self, database, label):
        with self.driver.session(database=database) as session:
            cypher_statement = "MATCH ()-[r:{}]-() DELETE r".format(label)
            session.write_transaction(self.neo4j_run_cypher, cypher_statement)

    def close_driver(self):
        self.driver.close()
