from __future__ import annotations

from .logger import Logger, LoggingLevels
from ..error_codes import ErrorCodes
from typing import TypeAlias
from pathlib import Path

import dataclasses
import hashlib
import struct
import enum
import json
import io

import types
import sys

MIN_SUPPORT = 0
MAX_SUPPORT = 0

MAXIMUM_PACK_VERSION = 1

PathLike: TypeAlias = str | Path

@dataclasses.dataclass
class SectionHeader:
    min_ver: int
    max_ver: int
    section_name: str

@dataclasses.dataclass
class MasterSectionHeader:
    section_name: str
    handler_func: function

class SectionHeaders(enum.Enum):
    FS = SectionHeader(1, None, "File System")
    HA = SectionHeader(1, None, "File Hash")

def dlcd_hander(self: Pack, count: int, build_path: Path, master_file: io.BytesIO):
    for _ in range(count):
        temp = struct.unpack("<I", master_file.read(4))[0]
        dlc_name: str = struct.unpack(f"<{temp}s", master_file.read(temp))[0].decode()

        temp = struct.unpack("<I", master_file.read(4))[0]
        folder: str = struct.unpack(f"<{temp}s", master_file.read(temp))[0].decode()
        self.file_replacements[dlc_name] = folder

        v = master_file.read(32)
        rpk_path = (build_path / (dlc_name + ".rpk"))
        if not rpk_path.exists():
            self.logger.log_debug(f"DLC {rpk_path.name} was not found, likely because it is optional.")
            continue

        self.logger.log_debug(f"Loading DLC data from pack {rpk_path.name}")
        dlc_data = DLC(rpk_path)
        dlc_data.validate()
        if dlc_data.hash != v:
            self.logger.write_to_log(f"The hash from {rpk_path.name} doesn't match what was stored in the master pack!",
                LoggingLevels.FATAL)
            self.logger.log_fatal(
                f"Failed to load pack {rpk_path.name} " + 
                f"({ErrorCodes.ERR_PACK_HASH_INVALID}: {ErrorCodes.ERR_PACK_HASH_INVALID.name})")
        self.logger.log_debug(f"DLC data for {rpk_path.name} was verified successfully!")

        self.dlc[dlc_name] = dlc_data

def mpfs_handler(self: Pack, count: int, build_path: Path, master_file: io.BytesIO):
    if not MasterSectionHeaders.DLCD in self.sections:
        self.logger.write_to_log("The Master File System table must be placed after the DLCD table!", LoggingLevels.FATAL)
        self.logger.log_fatal(f"The master pack failed to load! ({ErrorCodes.ERR_PACK_SECTION_NOT_LOADED}: {ErrorCodes.ERR_PACK_SECTION_NOT_LOADED.name})")

    file_tables = {}
    for _ in range(count):
        temp = struct.unpack("<I", master_file.read(4))[0]
        file_path, offset, size = struct.unpack(f"<{temp}sQQ", master_file.read(temp + 16))
        split_file_path = list(Path(file_path.decode()).parts)
        dlc_name = split_file_path[0]
        if not dlc_name in file_tables.keys():
            file_tables[split_file_path[0]] = {}

        split_file_path[0] = self.file_replacements[split_file_path[0]]
        split_file_path.insert(0, "assets")

        file_path = Path("/".join(split_file_path))
        file_tables[dlc_name][file_path] = (offset, size)
        self.file_links[file_path] = self.dlc[dlc_name]

    for dlc, table in file_tables.items():
        self.dlc[dlc].asset_table = table

class MasterSectionHeaders(enum.Enum):
    DLCD = MasterSectionHeader("DLC Data", dlcd_hander)
    MPFS = MasterSectionHeader("Master Pack File System", mpfs_handler)

class DLC:
    def __init__(self, path: Path):        
        self.file = path.open("rb")
        self.path = path

        self.sections = {}
        self.asset_table = {}

        self.logger = Logger("PACKER")

    def read_raw_file_data(self, offset, size) -> bytes:
        self.file.seek(self.sections[SectionHeaders.FS] + offset)
        hex_data = self.file.read(size)
        return struct.unpack(f"<{len(hex_data)}s", hex_data)[0]
    
    def read_file(self, path: PathLike) -> bytes:
        if isinstance(path, str):
            path = Path(path)

        offset, size = self.asset_table[path]
        return self.read_raw_file_data(offset, size)
    
    @property
    def files(self):
        return list(self.asset_table.keys())

    def validate(self):
        global MIN_SUPPORT, MAX_SUPPORT
        magic, ver, section_count = struct.unpack("<4sHH", self.file.read(8))
        if magic != b"RPK\x00" or ver > MAXIMUM_PACK_VERSION:
            self.logger.write_to_log(f"""
            Pack {self.path.name} has an invalid header!
            - Detected Header: {magic.decode().strip("\x00")} with a version of {ver}
            - Expected: {magic.decode().strip("\x00")} with a max version of {MAXIMUM_PACK_VERSION}""")
            self.logger.log_fatal(f"Failed to load pack {self.path.name} ({ErrorCodes.ERR_PACK_INVALID_HEADER}: {ErrorCodes.ERR_PACK_INVALID_HEADER.name})")

        if not MIN_SUPPORT <= ver <= MAX_SUPPORT:
            self.logger.write_to_log(
                f"""Pack {self.path.name} is outside the valid range defined by the master pack! 
                    - Detected pack version: {ver}
                    {f"- Supported version range: {MIN_SUPPORT}-{MAX_SUPPORT}" if MIN_SUPPORT != MAX_SUPPORT else f"- Supported Version: {MIN_SUPPORT}"}""", 
                    LoggingLevels.FATAL)
            self.logger.log_fatal(f"Failed to load pack {self.path.name} ({ErrorCodes.ERR_PACK_VERSION_UNSUPPORTED}: {ErrorCodes.ERR_PACK_VERSION_UNSUPPORTED.name})")

        for _ in range(section_count):
            section_header, size = struct.unpack("<4sQ", self.file.read(12))
            section_header = section_header.decode().upper().strip("\x00").strip()
            section_start = self.file.tell()

            try:
                header = SectionHeaders[section_header]
            except:
                self.logger.write_to_log(
                    f"""Unknown Section Identifier: {section_header} 
Valid identifiers:\n""" + "\n".join(f"  - {header_.name} ({header_.value.section_name})" for header_ in SectionHeaders), LoggingLevels.FATAL)
                self.logger.log_fatal(f"Failed to load pack {self.path.name} ({ErrorCodes.ERR_PACK_SECTION_UNKNOWN}: {ErrorCodes.ERR_PACK_SECTION_UNKNOWN.name})")

            if not header.value.min_ver <= ver and ver <= (header.value.max_ver if header.value.max_ver else float("inf")):
                self.logger.write_to_log(
                    f"""The section {section_header} ({header.value.section_name}) is not valid for pack version {ver}! 
                        - It was introduced in version {header.value.min_ver}{f", and was deprecated in version {header.value.max_ver}!" if header.value.max_ver != None else "!"}""", LoggingLevels.FATAL)
                self.logger.log_fatal(f"Failed to load pack {self.path.name} ({ErrorCodes.ERR_PACK_SECTION_NOT_ALLOWED}: {ErrorCodes.ERR_PACK_SECTION_NOT_ALLOWED.name})")

            if header == SectionHeaders.HA:
                detected_hash = self.file.read(32)
                self.file.seek(0)
                content = self.file.read()
                file_hash = hashlib.sha256(content[:section_start-12] + content[size + section_start:]).digest()
                if detected_hash != file_hash:
                    self.logger.write_to_log(
                        f"""The file hash for {self.path.name} doesn't match the detected hash!
                        - Detected: {int.from_bytes(detected_hash)}
                        - Expected: {int.from_bytes(file_hash)}""", 
                        LoggingLevels.FATAL)
                    self.logger.log_fatal(
                        f"Failed to load pack {self.path.name} " +
                        f"({ErrorCodes.ERR_PACK_HASH_INVALID}: {ErrorCodes.ERR_PACK_HASH_INVALID.name})")
                    
                self.hash = detected_hash

            self.sections[header] = section_start
            self.file.seek(section_start + size)

    def close(self):
        self.file.close()

class Pack:
    _instance = None
    _initalized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Pack, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwds):
        if Pack._initalized:
            return
        
        self.logger = Logger("PACKER")
        self.strict = kwds.pop("strict", True)
        
        global MIN_SUPPORT, MAX_SUPPORT
        build_path = Path("data")
        master_file = open(build_path / "mdlc.mrpk", "rb")
        magic, MIN_SUPPORT, MAX_SUPPORT, section_count = struct.unpack("<4sHHI", master_file.read(12))

        self.dlc: dict[str, DLC] = {}
        self.file_replacements = {}
        self.sections = set()

        self.file_links: dict[Path, DLC] = {}

        if magic != b"MRPK":
            self.logger.write_to_log("The master pack's header is invalid!",
                LoggingLevels.FATAL) 
            self.logger.log_fatal(f"The master pack failed to load! ({ErrorCodes.ERR_PACK_INVALID_HEADER}: {ErrorCodes.ERR_PACK_INVALID_HEADER.name})")

        # RoWiz (5/4/26):
        # No longer hardcoding section positions. They can now be in (almost) any order, excluding a few specific sections.
        for _ in range(section_count):
            header_key, count = struct.unpack("<4sI", master_file.read(8))
            header_key: str = header_key.decode().upper().strip("\x00").strip()
            
            header = MasterSectionHeaders[header_key]
            header.value.handler_func(self, count, build_path, master_file)

            self.sections.add(header)

        Pack._initalized = True

        # Behavior loading
        behavior_globals = {}
        self.behavior_globals = behavior_globals

        self.module_to_path = lambda m: Path(*m.split("."))
        def get_behavior_data(module: str, globals={}, locals=None, fromlist=(), level=0) -> types.ModuleType:
            Logger("PACK BEHAVIORS").write_to_log(f"""
Importing {module}
- With Fromlist: {fromlist}
- At Level     : {level}
""", LoggingLevels.DEBUG)
            if level == 0 and not module.startswith("assets"):
                return __import__(module, globals, locals, fromlist, level)

            module = ".".join(submodule[:len(submodule)-(level-1)]) + "." + module if len(submodule:=globals.get("__package__", "").split(".")) > 0 else module

            if module in sys.modules:
                Logger("PACK BEHAVIORS").write_to_log(f"""
Importing already initalized module: {module}
- With Fromlist: {fromlist}
""")
                return sys.modules[module]
            
            file_path = self.module_to_path(module)
            data = self.file_links[suffixed_path:=file_path.with_suffix(".py")].read_file(suffixed_path)

            behavior_module = types.ModuleType(module)
            behavior_module.__package__ = ".".join(module.split(".")[:-1])

            import builtins
            behavior_module_builtins = builtins.__dict__.copy()
            behavior_module_builtins["__import__"] = get_behavior_data
            behavior_module.__dict__["__builtins__"] = behavior_module_builtins

            sys.modules[module] = behavior_module

            compiled_code = compile(data, file_path, "exec")
            exec(compiled_code, behavior_module.__dict__)

            return behavior_module
        
        self.__get_behavior_data = get_behavior_data
        
    @property
    def files(self):
        return list(self.file_links.keys())
    
    def has_dlc(self, dlc_name: str):
        if dlc_name in self.dlc.keys():
            return self.dlc[dlc_name]
        
        else:
            return False
        
    def get_dlc(self, dlc_name: str):
        if not dlc_name in self.dlc.keys():
            if self.strict:
                self.logger.log_fatal(f"Cannot return data for {dlc_name}, as it does not exist!")
            
            else:
                return None
        
        return self.dlc[dlc_name]
    
    def __get_decorator(func):
        def wrapper(self, *args):
            file_path = args[0]
            if isinstance(file_path, str):
                file_path = Path(file_path)

            return func(self, file_path, *args[1:])

        return wrapper 

    @__get_decorator
    def get_contents(self, file_path: PathLike):
        return self.file_links[file_path].read_file(file_path).decode()
    
    @__get_decorator
    def get_raw(self, file_path: PathLike):
        return self.file_links[file_path].read_file(file_path)
    
    @__get_decorator
    def read_json(self, file_path: PathLike):
        data = self.file_links[file_path].read_file(file_path)
        return json.loads(data.decode())
    

    def load_behavior(self, module: str, behavior_class: str):
        if not module in sys.modules:
            module_data = self.__get_behavior_data(module)
        else:
            module_data = sys.modules[module]

        if hasattr(module_data, behavior_class):
            return getattr(module_data, behavior_class)
        else:
            Logger("PACK BEHAVIORS").log_fatal(f"{module} is missing requested class {behavior_class}")