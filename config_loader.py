import yaml

def load_config(file_path: str) -> dict:
    """Carga la configuración desde un archivo YAML."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)
