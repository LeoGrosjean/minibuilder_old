import json
from pathlib import Path


def load_json(json_path, occurence=1):
    occurence = json_path.count(".") - 1
    with open(str(Path(json_path.replace('.', '/', occurence)))) as f:
        return json.load(f)
