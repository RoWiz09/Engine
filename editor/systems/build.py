from . import global_vars

from typing import TYPE_CHECKING, TypeAlias, Any
if TYPE_CHECKING:
    from ghost_engine.core.logger import Logger
    from ghost_engine.scripting import behavior

else:
    Logger: TypeAlias = Any

from pathlib import Path

from . import global_vars as modules
from .task_scheduler import TaskScheduler

import subprocess
import os, struct
import importlib
import tempfile
import inspect
import hashlib
import json
import sys
import io

def make_module(logger: Logger, module_name: str, tmp_path: Path, dlc_path: Path):
    module_files = []

    for dirpath, _, filenames in dlc_path.walk():
        for fn in filenames:
            if not fn.endswith(".py"):
                continue

            if "__init__.py" in fn:
                logger.log_fatal("Modules cannot contain an __init__.py file!")

            filepath = dirpath / fn
            module_path = tmp_path / dirpath.relative_to("assets")
            module_path.mkdir(parents=True, exist_ok=True)
            module_file_path = module_path / fn
            
            module_files.append(".".join((dirpath / fn).parts).removesuffix(".py"))

            module_file_path.write_text(filepath.read_text())

    init_file_path = tmp_path / module_name / "__init__.py"
    init_file_path.write_text("\n".join(f"import {file}" for file in module_files))

    build_command = [
        'py', '-m', 'nuitka',
        '--mode=package', '--remove-output', "--no-pyi-file", f'--output-dir={Path(os.environ["project-path"]) / 'dist' / os.environ['project'] / 'data'}', 
        str(tmp_path / module_name)
    ]
    subprocess.run(build_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=tmp_path)

def build_task(logger: Logger):
    """
        DO NOT CALL THIS!
    """
    logger.log_debug("Building Game...")
    
    dlcs = ["GhostEngine"]
    with open(".rproj") as project_file:
        project_data = json.load(project_file)
        dlcs.extend([val['root'] for val in project_data["dlc"].values()])
    
    assets_path = Path("assets")
    def check_for_script(dlc_path: Path):
        for dirpath, dirnames, filenames in dlc_path.walk():
            for filename in filenames:
                if filename.endswith(".py"):
                    return True
                
        return False

    # with tempfile.TemporaryDirectory() as modules_tmpdir:
    #     (tmp_path := Path(modules_tmpdir) / 'assets').mkdir()
    #     for dlc in dlcs:
    #         dlc_path = assets_path / dlc
            
    #         if not check_for_script(dlc_path):
    #             continue
            
    #         (tmp_path / dlc).mkdir(parents=True)
    #         make_module(logger, dlc, tmp_path, dlc_path)

    #     build_command = [
    #         'py', '-m', 'nuitka', '--remove-output',
    #         '--deployment', '--standalone', f'--include-package-data={str(tmp_path)}', f'--output-dir={Path('dist') / os.environ['project']}',
    #         os.environ['project']+'.py'
    #     ]
    #     subprocess.run(build_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    logger.log_debug("Writing asset packs...")

    # Pack the game assets
    write_packs(logger)

    logger.log_info("Game built successfully!")

def build_game(*dynamic_libs):
    TaskScheduler.schedule_task(build_task)

def write_packs(logger: Logger):
    assets_path = Path("assets")
    output_path = "dist" / Path(f"{os.environ["project"]}") / "data"
    output_path.mkdir(parents=True, exist_ok=True)
    dlcs: list[tuple[str, dict]] = [("edlc", {"root": "GhostEngine"})]
    with open(".rproj") as project_file:
        project_data = json.load(project_file)
        dlcs.extend(project_data["dlc"].items())

    logger.log_info(f"Discovered DLC's: {", ".join(os.path.split(dlc[1]['root'])[1] for dlc in dlcs)}")
    
    file_positions = {}

    for dlc_name, dlc_data in dlcs:
        logger.log_info(f"Loading assets for DLC: {os.path.split(dlc_data['root'])[1]}")

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
                if file.endswith(".py"):
                    continue

                file_path = dirpath / file
                content = file_path.read_text()

                file_positions[str(dlc_name / file_path.relative_to(assets_path/dlc_root))] = (len(file_bytes), len(content))
                file_bytes += struct.pack(f"<{len(content)}s", content.encode())
        
        logger.log_info("Writing assets to RPK file...")
        dlc_file.write(struct.pack("<Q", len(file_bytes)) + file_bytes)
        dlc_file.flush()
        
        dlc_file.seek(0)
        hash_ = hashlib.sha256(dlc_file.read()).digest()
        dlc_file.write(struct.pack("<4sQ", b"HA", 32) + hash_)
        dlc_data["hash"] = hash_

    logger.log_info("Writing the Master Pack file")
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
