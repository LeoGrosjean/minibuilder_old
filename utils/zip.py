import io
from zipfile import ZipFile


def write_zip(file_paths):
    data = io.BytesIO()
    with ZipFile(data, 'w') as zip:
        # writing each file one by one
        for file, name in file_paths:
            zip.write(file, name + ".stl")
    data.seek(0)
    return data