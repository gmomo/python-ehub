"""
Loads the config.yaml file into a Python dictionary as `SETTINGS`.
"""
import yaml

with open("config.yaml", "r") as f:
    SETTINGS = yaml.safe_load(f)
