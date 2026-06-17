import os
import sys
import socket
import struct
import json
import time

import enum

from . import global_vars

PRESENCE_SHOW_SCENE = 1000

CLIENT_ID = "1510115212055937075" 
class DiscordRichPresence:
    def __init__(self, client_id: str, flags = 0):
        self.client_id = client_id
        self.socket = None

        self.start_time = int(time.time())
        self.flags = flags
        
    def _get_ipc_path(self) -> str:
        if sys.platform == "win32":
            return r"\\.\pipe\discord-ipc-0"
        
        for env_var in ["XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP"]:
            path = os.environ.get(env_var)
            if path and os.path.exists(os.path.join(path, "discord-ipc-0")):
                return os.path.join(path, "discord-ipc-0")
        
        if os.path.exists("/tmp/discord-ipc-0"):
            return "/tmp/discord-ipc-0"
            
        raise FileNotFoundError("Could not find a running Discord client IPC socket.")

    def connect(self):
        ipc_path = self._get_ipc_path()
        
        if sys.platform == "win32":
            self.socket = open(ipc_path, "wb+", buffering=0)
        else:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(ipc_path)
            
        handshake_payload = {"v": 1, "client_id": self.client_id}
        self._send_packet(opcode=0, payload=handshake_payload)
        
        self._read_response()

    def _send_packet(self, opcode: int, payload: dict):
        payload_json = json.dumps(payload).encode("utf-8")
        header = struct.pack("<II", opcode, len(payload_json))
        
        if sys.platform == "win32":
            self.socket.write(header + payload_json)
        else:
            self.socket.sendall(header + payload_json)

    def _read_response(self) -> dict:
        if sys.platform == "win32":
            header = self.socket.read(8)
            if not header: return {}
            opcode, length = struct.unpack("<II", header)
            payload = self.socket.read(length)
        else:
            header = self.socket.recv(8)
            if not header: return {}
            opcode, length = struct.unpack("<II", header)
            payload = self.socket.recv(length)
            
        return json.loads(payload.decode("utf-8"))

    def set_activity(self, activity_data: dict):
        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity_data
            },
            "nonce": str(time.time())
        }
        self._send_packet(opcode=1, payload=payload)
        return self._read_response()

    def start_handling_activity(self):
        import threading
        def handler(self: DiscordRichPresence):
            while True:
                state_data = [f"Working on project: {os.environ.get("project", "")}"]
                if self.flags & PRESENCE_SHOW_SCENE:
                    state_data.append(f'Current Scene: {global_vars.scene_manager().cur_scene}')

                presence_data = {
                    "name": "Ghost Engine Editor",
                    "state": "|".join(state_data),
                    "details": f"Developing...",
                    "timestamps": {
                        "start": self.start_time
                    },
                    "assets": {}
                }

                self.set_activity(presence_data)
                time.sleep(5)

        t = threading.Thread(target=handler, args=(self,), daemon=True)
        t.start()

    def close(self):
        if self.socket:
            self.socket.close()

