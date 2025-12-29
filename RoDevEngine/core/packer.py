from __future__ import annotations

from .logger import Logger

import io

import os
import struct
import json

class Pack:
    _instance = None
    _initalized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Pack, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Pack._initalized:
            self.files : list[str] = []
            with open("pak_master.mrpk", "rb") as master_pak:
                # Read and validate header
                header_struct = struct.Struct("<4sHHH")
                magic, version, entry_count, packs_offset = header_struct.unpack(master_pak.read(header_struct.size))
                if magic != b"RPKM":
                    raise ValueError("Invalid pak master file.")

                # Read TOC entries
                toc_entries = {}
                for _ in range(entry_count):
                    name_length = struct.unpack("<H", master_pak.read(2))[0]
                    name = master_pak.read(name_length).decode()
                    file_length = struct.unpack("<H", master_pak.read(2))[0]
                    file_name = master_pak.read(file_length).decode()
                    offset = struct.unpack("<I", master_pak.read(4))[0]
                    toc_entries[name] = {"file": file_name, "offset": offset}

                self.packs : dict[str, io.BufferedReader] = {}
                for entry in toc_entries.values():
                    if entry["file"] not in self.packs:
                        self.packs[entry["file"]] = open(entry["file"], "rb")

                self.toc = {name: entry for name, entry in toc_entries.items()}
                self.files.extend([name for name in toc_entries.keys()])

        Pack._initalized = True
    
    def get(self, asset_name: str) -> bytes:
        if asset_name not in self.toc:
            raise ValueError(f"Asset {asset_name} not found in the Table of Contents...")

        entry = self.toc[asset_name]
        pack_file = self.packs[entry["file"]]
        pack_file.seek(entry["offset"])

        name_length = struct.unpack("<H", pack_file.read(2))[0]
        pack_file.read(name_length)  # Skip name
        data_length = struct.unpack("<I", pack_file.read(4))[0]
        data = pack_file.read(data_length)

        return data
    
    def get_string(self, asset_name: str) -> str:
        data = self.get(asset_name)
        return data.decode("utf-8")
    
    def get_as_json_dict(self, asset_name: str) -> dict:
        data = self.get(asset_name).decode()
        json_data = json.loads(data)
        if not isinstance(json_data, dict):
            Logger("CORE").log_warning(f"File data at {asset_name} is not a dictionary!")
            return None
        
        return json_data

    @staticmethod
    def write_packs():
        """
            Used when building a project made in the engine. \n
            TODO: Add DLC Packing
        """

        assets = {}
        for dirpath, dirnames, filenames in os.walk("assets/"):
            for filename in filenames:
                # Ignore configuration files
                if filename.endswith(".rconfig"):
                    continue

                with open(os.path.join(dirpath, filename), "rb") as f:
                    # Ignore __pycache__ directories
                    if dirpath.endswith("__pycache__"):
                        continue

                    data = f.read()

                    assets[os.path.join(dirpath, filename)] = data

        # Keep track of offsets for TOC
        toc_entries = []
        with open("pak_0.rpk", "wb+") as pak_file:
            # --- Write header ---
            # Magic(4s) + version(H) + asset_count(H)
            header_struct = struct.Struct("<4sHH")
            magic = b"RPK0"
            version = 1
            asset_count = len(assets)
            pak_file.write(header_struct.pack(magic, version, asset_count))

            # --- Write engine asset blocks ---
            for asset_name, asset_data in assets.copy().items():
                if "GhostEngine" not in asset_name:
                    # Only pack GhostEngine files in pak_0.rpk
                    continue

                # Record current offset for this asset
                toc_entries.append(
                    {
                        "name": asset_name.encode("utf-8"),
                        "offset": pak_file.tell(),
                        "file": pak_file.name.encode("utf-8")
                    }
                )

                # Write: [name_length (H)][name bytes][data_length (I)][data bytes]
                name_bytes = asset_name.encode("utf-8")
                pak_file.write(struct.pack("<H", len(name_bytes)))  # 2 bytes for name length
                pak_file.write(name_bytes)                           # variable-length name
                pak_file.write(struct.pack("<I", len(asset_data)))   # 4 bytes for data length
                pak_file.write(asset_data)                           # actual asset data

                assets.pop(asset_name)

        with open("pak_1.rpk", "wb+") as pak_file:
            # --- Write header ---
            # Magic(4s) + version(H) + asset_count(H)
            header_struct = struct.Struct("<4sHH")
            magic = b"RPK0"
            version = 1
            asset_count = len(assets)
            pak_file.write(header_struct.pack(magic, version, asset_count))

            # --- Write engine asset blocks ---
            for asset_name, asset_data in assets.items():
                # Record current offset for this asset
                toc_entries.append(
                    {
                        "name": asset_name.encode("utf-8"),
                        "offset": pak_file.tell(),
                        "file": pak_file.name.encode("utf-8")
                    }
                )

                # Write: [name_length (H)][name bytes][data_length (I)][data bytes]
                name_bytes = asset_name.encode("utf-8")
                pak_file.write(struct.pack("<H", len(name_bytes)))  # 2 bytes for name length
                pak_file.write(name_bytes)                           # variable-length name
                pak_file.write(struct.pack("<I", len(asset_data)))   # 4 bytes for data length
                pak_file.write(asset_data)                           # actual asset data

        # --- Write the master pak, which contains the TOC ---
        with open("pak_master.mrpk", "wb+") as master_pak:
            # Magic (4s), version (H), entry count (H)
            header_struct = struct.Struct("<4sHH")
            magic = b"RPKM"
            version = 1
            master_pak.write(header_struct.pack(magic, version, len(toc_entries)))

            byte_content = b""

            # Each entry in the TOC (length of entry name (H), entry name, length of pack name (H), pack name, and offset (I))
            for entry in toc_entries:
                byte_content += struct.pack("<H", len(entry["name"].replace(b"\\", b"/")))
                byte_content += entry["name"].replace(b"\\", b"/")
                byte_content += struct.pack("<H", len(entry["file"]))
                byte_content += entry["file"]
                byte_content += struct.pack("<I", entry["offset"])

            packs_offset = header_struct.size + 2 + len(byte_content)
            master_pak.write(struct.pack("<H", packs_offset))

            master_pak.write(byte_content)