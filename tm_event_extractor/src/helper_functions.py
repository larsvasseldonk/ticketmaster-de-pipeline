from pathlib import Path


def get_root_project_dir() -> Path:
    """Get the project root folder path."""

    return Path(__file__).parent.parent