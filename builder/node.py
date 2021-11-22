import json

import networkx as nx
from networkx.readwrite import json_graph

def read_node_link_json(filename):
    with open(filename) as f:
        js_graph = json.load(f)
    return json_graph.node_link_graph(js_graph, directed=True)




