from py2neo import Graph

class py2NeoUtil:
    def __init__(self):
        host = "neo4j://172.16.231.80:7687"
        user = "neo4j"
        password = "123456"
        self.driver = Graph(host, auth=(user, password))

    def run_cypher(self, cypher):
        result_list = self.driver.run(cypher).data()
        return result_list