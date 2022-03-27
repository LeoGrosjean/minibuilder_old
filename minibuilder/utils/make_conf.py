import os
from pathlib import Path


def build_dict_path():
    di = {}
    for builder in os.listdir("data"):
        di[builder] = {}
        for category in os.listdir(f'data/{builder}/configuration'):
            path = Path(f'data/{builder}/configuration/{category}')
            if path.is_dir():
                di[builder][category] = list(os.listdir(f'data/{builder}/configuration/{category}'))
    return di
