#!/usr/bin/env python3
import os
from pathlib import Path

def print_tree(directory: Path, prefix: str = "", show_hidden: bool = True):
    """Print a visual tree structure of the directory."""
    path = Path(directory)
    if not path.exists():
        print(f"Directory '{path}' does not exist.")
        return
    if not path.is_dir():
        print(f"'{path}' is not a directory.")
        return

    # Get all entries (files and folders), sorted
    entries = [p for p in path.iterdir() if show_hidden or not p.name.startswith('.')]
    entries.sort(key=lambda p: (p.is_file(), p.name.lower()))

    # Count connectors
    pointers = ["├── "] * (len(entries) - 1) + (["└── "] if entries else [])

    for pointer, entry in zip(pointers, entries):
        print(f"{prefix}{pointer}{entry.name}")
        if entry.is_dir():
            extension = "│   " if pointer == "├── " else "    "
            print_tree(entry, prefix + extension)

if __name__ == "__main__":
    current_dir = Path(".")
    print(f"Directory structure of: {current_dir.resolve()}")
    print_tree(current_dir, show_hidden=True)