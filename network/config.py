import yaml
import os

def load_config(path=None):
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
