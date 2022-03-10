def find_vertices(mesh, *args):
    li = []
    for i, (x, y, z) in enumerate(mesh.vertices):
        for value in args:
            if value == [x,y,z]:
                print(i)
                li.append(i)
    if len(li) == 1:
        return {"vertex": li[0]}
    else:
        return {"vertex_list": li}
