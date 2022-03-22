import os
from pathlib import Path

import requests

access_keyword = "?access_token="
api_token = "7f7903cc31ade13b118d46be638de9bd"
BASE_URL = "https://api.thingiverse.com/things"


def get_thing_download_files(thing_id, access_token=api_token):
    param_access_token = get_access_token_parameter(access_token)
    files_url = "{0}/{1}/files/{2}".format(BASE_URL, thing_id,
                                           param_access_token)
    r = requests.get(url=files_url)
    return r.json()


def get_access_token_parameter(ACCESS_TOKEN):
    return "?access_token={0}".format(ACCESS_TOKEN)


def download_object(thing_id, dest_file, access_token=api_token):
    s = requests.Session()
    file_name = Path(dest_file).name
    for file in get_thing_download_files(thing_id, access_token):
        if file_name == file.get('name'):
            download_link = file["download_url"] + access_keyword + api_token
            r = s.get(download_link)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            with open(dest_file, "wb") as code:
                code.write(r.content)
            print(f"File has been downloaded from Thingiverse to {dest_file} !")
            return True
    return False


