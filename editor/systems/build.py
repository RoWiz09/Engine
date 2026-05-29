from . import global_vars

from typing import TYPE_CHECKING
from types import MappingProxyType
if TYPE_CHECKING:
    from ghost_engine.scripting import behavior

from pathlib import Path
import os, struct
import importlib
import inspect
import hashlib
import json
import copy
import sys
import os

def build_game():
    print("Building the game...")

    # Build the executable using PyInstaller
    try:
        if os.system("py -m PyInstaller main.py") != 0:
            print("Failed to build the executable.")
    except Exception as e:
        print(f"Error during build: {e}")

    print("Writing asset packs...")

    # Pack the game assets
    write_packs()

    print("Game built successfully!")

def write_packs():
    """
        Used when building a project made in the engine. \n
        TODO: Add DLC Packing
    """

    assets_path = Path("assets")
    output_path = Path(f"dist/{os.environ["project"]}")
    output_path.mkdir(parents=True, exist_ok=True)
    dlcs: list[tuple[str, dict]] = [("edlc", {"root": "GhostEngine"})]
    with open(".rproj") as project_file:
        project_data = json.load(project_file)
        dlcs.extend(project_data["dlc"].items())
    
    file_positions = {}

    path_to_module = lambda p: str(p).replace(os.sep, ".").removesuffix(".py")
    if TYPE_CHECKING:
        behavior_type = behavior.Behavior
        exclude_from_build = behavior.EXCLUDED_FROM_BUILD

    else:
        behavior_type = getattr(sys.modules["ghost_engine.scripting.behavior"], "Behavior")
        exclude_from_build = getattr(sys.modules["ghost_engine.scripting.behavior"], "EXCLUDED_FROM_BUILD")

    for dlc_name, dlc_data in dlcs:
        dlc_root: str = dlc_data["root"]
        dlc_file_path = output_path / (dlc_name + ".rpk")
        dlc_file = dlc_file_path.open("wb+")
        dlc_file.write(struct.pack("<4sHH", b"RPK", 1, 2))
        dlc_file.write(struct.pack("<4s", b"FS"))
        file_bytes = b""
        for dirpath, _, files in (assets_path / dlc_root).walk():
            if str(dirpath).endswith("__pycache__"):
                continue

            for file in files:
                file_path = (dirpath / file)
                if not file.endswith(".py"):
                    with open(file_path) as f:
                        content = f.read()
                
                else:
                    module = importlib.import_module(path_to_module(file_path))
                    module_lines = inspect.getsource(module).splitlines()

                    deleted_data = []
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if obj.__module__ != module.__name__:
                            continue

                        orig_dict = dict(obj.__dict__)
                        for func in exclude_from_build:
                            if not func.__name__ in orig_dict.keys():
                                continue
                            
                            lines, start = inspect.getsourcelines(orig_dict[func.__name__])
                            deleted_data.append((start - 1, len(lines) + start - 1))

                    deleted_data.sort(key=lambda se: se[0])
                    for start, end in deleted_data:
                        module_lines = module_lines[:start] + module_lines[end:]
                    
                    content = "\n".join(module_lines)

                file_positions[str(dlc_name / file_path.relative_to(assets_path/dlc_root))] = (len(file_bytes), len(content))
                file_bytes += struct.pack(f"<{len(content)}s", content.encode())
                
        dlc_file.write(struct.pack("<Q", len(file_bytes)) + file_bytes)
        dlc_file.flush()
        
        dlc_file.seek(0)
        hash_ = hashlib.sha256(dlc_file.read()).digest()
        dlc_file.write(struct.pack("<4sQ", b"HA", 32) + hash_)
        dlc_data["hash"] = hash_

    master = output_path / "mdlc.mrpk"
    master_file = master.open("wb+")

    master_file.write(struct.pack("<4sHHI", b"MRPK", 1, 1, 2))
    master_file.write(struct.pack("<4sI", b"DLCD", len(dlcs)))
    for dlc_name, dlc_data in dlcs:
        master_file.write(
            struct.pack(
                f"<I{len(dlc_name)}sI{len(dlc_data["root"])}s", 
                len(dlc_name), dlc_name.encode(), 
                len(dlc_data["root"]), dlc_data["root"].encode()
            ) + dlc_data["hash"])
        
    master_file.write(struct.pack("<4sI", b"MPFS", len(file_positions)))
    for path, file_data in file_positions.items():
        offset, size = file_data
        master_file.write(struct.pack(f"<I{len(path)}sQQ", len(path), path.encode(), offset, size))
