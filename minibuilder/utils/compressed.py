import os
import shutil
from pathlib import Path

import patoolib

from minibuilder.forms.home import get_data_folder


def extract_nested_compress(builder_name, file_filename):
    try:
        if file_filename not in os.listdir(f"{get_data_folder()}/{builder_name}/uploaded/"):
            patoolib.extract_archive(f"{get_data_folder()}/{builder_name}/uploaded/{file_filename}", outdir=f"{get_data_folder()}/{builder_name}/uploaded/")
            os.remove(f"{get_data_folder()}/{builder_name}/uploaded/{file_filename}")
            print(f"all files has been extracted from {get_data_folder()}/{builder_name}/uploaded/{file_filename}")

    except Exception as e:
        print(f'{file_filename} has been added to data/{builder_name}/uploaded/')

    flatten_dir(f"{get_data_folder()}/{builder_name}/uploaded/", f"{get_data_folder()}/{builder_name}/uploaded/")

    while set(patoolib.ArchiveFormats) & { x.split('.')[-1] for x in os.listdir(f"{get_data_folder()}/{builder_name}/uploaded/")}:
        for file in os.listdir(f"{get_data_folder()}/{builder_name}/uploaded/"):
            if file.split('.')[-1] in patoolib.ArchiveFormats and file in os.listdir(f"{get_data_folder()}/{builder_name}/uploaded/"):
                patoolib.extract_archive(f"{get_data_folder()}/{builder_name}/uploaded/{file}",
                                         outdir=f"{get_data_folder()}/{builder_name}/uploaded/")
                os.remove(f"{get_data_folder()}/{builder_name}/uploaded/{file}")
                flatten_dir(f"{get_data_folder()}/{builder_name}/uploaded/", f"{get_data_folder()}/{builder_name}/uploaded/")


def getfiles(path):
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for name in files:
                yield os.path.join(root, name)
    else:
        yield path


def flatten_dir(from_dir, dest_dir):
    for f in getfiles(from_dir):
        filename = Path(f)
        if os.path.isfile(str(filename)):
            try:
                shutil.move(f, dest_dir + filename.name)
            except Exception as e:
                print(e)

    for file in os.listdir(dest_dir):
        if os.path.isdir(dest_dir + file):
            shutil.rmtree(dest_dir + file)

