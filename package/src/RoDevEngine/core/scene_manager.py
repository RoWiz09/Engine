from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine.object import Object 

from RoDevEngine.core.logger import Logger

from dataclasses import dataclass

import os, json, importlib, glfw

@dataclass(frozen=True)
class SceneInfo:
    scene_name: str
    scene_index: int

class SceneManager:
    def __init__(self, compiled: bool = True):
        self.compiled = compiled
        self.scenes = self.get_scenes()
        self.game_objects: list[Object] = []

        self.last_time = glfw.get_time()
        self.accumulator = 0.0

        # Load first scene by default
        self.load_scene_index(0)

    def get_scenes(self) -> dict[str, str]:
        """Returns dict of scene_name -> file_path"""
        scenes = {}
        if not self.compiled:
            for dirpath, _, filenames in os.walk("assets/"):
                for filename in filenames:
                    if filename.endswith(".rscene"):
                        scenes[filename.removesuffix(".rscene")] = os.path.join(dirpath, filename)
        return scenes

    def _instantiate_scene_objects(self, scene_path: str) -> list[Object]:
        scene_objects = []
        with open(scene_path) as scene_file:
            scene_data = json.load(scene_file)
            game_objects: list[dict] = scene_data["objects"]

            for obj_data in game_objects:
                object_name = obj_data["name"]
                game_object = Object(object_name)
                scripts = []

                for comp_data in obj_data.get("components", []):
                    module = importlib.import_module(comp_data["module"])
                    cls = getattr(module, comp_data["class"])
                    vars_data = comp_data.get("vars", {})

                    if issubclass(cls, Behavior):
                        behavior = cls(game_object)
                        for var_name, value in vars_data.items():
                            setattr(behavior, var_name, value)
                        scripts.append(behavior)
                    else:
                        Logger("CORE").log_warning(
                            f"Script {cls.__name__} is not a subclass of Behavior and cannot be applied to {object_name}!"
                        )

                game_object.add_components(*scripts)
                scene_objects.append(game_object)


        return scene_objects

    def load_scene(self, scene_name: str):
        scene_index = list(self.scenes.keys()).index(scene_name)
        self.load_scene_index(scene_index)

    def load_scene_index(self, scene_index: int):
        scene_name = list(self.scenes.keys())[scene_index]
        scene_path = self.scenes[scene_name]

        # Call unload callbacks on current scene before switching
        scene_info = SceneInfo(scene_name, scene_index)
        for obj in self.game_objects:
            for script in obj.components:
                script.on_scene_unload(scene_info)

        # Load new scene objects
        self.game_objects = self._instantiate_scene_objects(scene_path)
        Logger("SCENE MANAGEMENT").log_debug(f"Loaded scene {scene_info}")

        # Call load callbacks
        for obj in self.game_objects:
            for script in obj.components:
                script.on_scene_load(scene_info)

    def update_scene(self):
        time = glfw.get_time()
        frame_dur = time - self.last_time
        self.last_time = time
        self.accumulator += frame_dur

        while self.accumulator >= 1/50:
            for obj in self.game_objects:
                obj.fixed_update()
            self.accumulator -= 1/50
