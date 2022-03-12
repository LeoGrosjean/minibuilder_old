def find_vertices(mesh, *args):
    li = []
    # TODO do something omg
    if "face" in args[0][0]:
        for i, facet in enumerate(mesh.facets):
            if int(args[0][0].split(':')[-1]) in facet:
                return {"facet": i}
    for i, (x, y, z) in enumerate(mesh.vertices):
        for value in args:
            if value == [x, y, z]:
                print(i)
                li.append(i)
    if len(li) == 1:
        return {"vertex": li[0]}
    else:
        return {"vertex_list": li}

