import numpy as np
def find_vertices(mesh, *args):
    li = []
    # TODO do something omg
    try:
        if "face" in args[0][0]:
            for i, facet in enumerate(mesh.facets):
                if int(args[0][0].split(':')[-1]) in facet:
                    return {"facet": i}
            return "ERROR"
    except Exception as e:
        print("processing vertice...")
    for i, (x, y, z) in enumerate(mesh.vertices):
        for value in args:
            check = np.array(value) - np.array([x, y, z])
            if (-10e-04 < check).all() and (check < 10e-04).all():
                print(i)
                li.append(i)
    if len(li) == 1:
        return {"vertex": li[0]}
    else:
        return {"vertex_list": li}

