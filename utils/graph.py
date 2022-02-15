def get_successors(graph, node):
    result = []
    children = list(graph.successors(node))
    if children:
        result.extend(children)
        for child in children:
            result.extend(get_successors(graph, child))
    return result