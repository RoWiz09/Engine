from RoDevEngine.object import Object 

import os, json, importlib, glfw

class SceneManager:
    def __init__(self, compiled:bool = True):
        self.compiled = compiled

        self.scenes = self.get_scenes()
        self.game_objects = []

        self.last_time = glfw.get_time()

    def get_scenes(self):
        """
            Gets a dict of all scenes and their paths (Unless compiled, where it will be the position and file the scene is in).
            Returns:
                scenes (dictionary): The scenes in the project
        """ 
        scenes = {}
        if self.compiled is False:
            for dirpath, dirname, filenames in os.walk("assets/"):
                for filename in filenames:
                    if not filename.endswith(".rscene"):
                        continue

                    scenes[filename.removesuffix(".rscene")] = os.path.join(dirpath, filename)

        return scenes

    def load_scene(self, scene_name: str):
        scene_objects = []

        if not self.compiled:
            scene_path = self.scenes[scene_name]

            with open(scene_path) as scene_file:
                scene_data = json.load(scene_file)

                game_objects: dict[str, dict] = scene_data["objects"]

                for object_name, obj_data in game_objects.items():
                    scripts = []

                    # Expect "components" to be a list of behaviors
                    for comp_data in obj_data["components"]:
                        module_name = comp_data["module"]
                        class_name = comp_data["class"]
                        vars_data = comp_data.get("vars", {})

                        # Import module + class
                        module = importlib.import_module(module_name)
                        cls = getattr(module, class_name)

                        # Instantiate
                        behavior = cls()

                        # Assign variables
                        for var_name, value in vars_data.items():
                            setattr(behavior, var_name, value)

                        scripts.append(behavior)

                    # Build game object with scripts
                    game_object = Object(object_name, *scripts)
                    scene_objects.append(game_object)

        self.game_objects = scene_objects

    def update_scene(self):
        time = glfw.get_time()
