from RoDevEngine.rendering.shader_program import ShaderProgram
from RoDevEngine.rendering.material import Material
from RoDevEngine.scripts.behavior import Behavior
from RoDevEngine.core.transform import Transform
from RoDevEngine.core.packer import Pack
from RoDevEngine.object import Object 

from pyglm import glm

import PIL.Image as image

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
        if self.compiled:
            self.pack = Pack()

        self.scenes = self.get_scenes()
        shaders = self.get_shaders()
        self.materials = self.get_materials(shaders)
        self.game_objects: list[Object] = []

        self.scripts = {}

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

        else:
            for file in self.pack.files:
                if file.endswith(".rscene"):
                    name = os.path.split(file)[-1].removesuffix(".rscene")

                    scenes[name] = file

        return scenes

    def get_shaders(self) -> dict[str, ShaderProgram]:
        """
            Returns dict of shader_name -> file_path
        """
        shaders = {}
        if not self.compiled:
            for dirpath, _, filenames in os.walk("assets/"):
                for filename in filenames:
                    if filename.endswith(".rshader"):
                        # Get the shader name without the .rshader extension
                        name = filename.removesuffix(".rshader")
                        
                        # Load the shader file
                        with open(os.path.join(dirpath, filename)) as shader_file:
                            shader_data = json.load(shader_file)
                            vertex_path = shader_data.get("VertexShader", "")
                            fragment_path = shader_data.get("FragmentShader", "")
                            if not vertex_path or not fragment_path:
                                continue
                            with open(vertex_path) as f:
                                vertex_src = f.read()
                            with open(fragment_path) as f:
                                fragment_src = f.read()
                            
                            if vertex_path and fragment_path:
                                shaders[name] = ShaderProgram(vertex_src, fragment_src)
                                shaders[name].use()
                            else:
                                Logger("SCENE MANAGEMENT").log_warning(f"Shader {name} is missing VertexShader or FragmentShader fields.")
        
        else:
            for file in self.pack.files:
                if file.endswith(".rshader"):
                    name = os.path.split(file)[-1].removesuffix(".rshader")

                    shader_data = self.pack.get_as_json_dict(file)
                    vertex_path = shader_data.get("VertexShader", "")
                    fragment_path = shader_data.get("FragmentShader", "")
                    
                    if vertex_path and fragment_path:
                        shaders[name] = ShaderProgram(self.pack.get(vertex_path), self.pack.get(fragment_path))
                        shaders[name].use()
                    else:
                        Logger("SCENE MANAGEMENT").log_warning(f"Shader {name} is missing VertexShader or FragmentShader fields.")
                        
        return shaders
    
    def get_materials(self, shaders:dict[str, ShaderProgram]) -> dict[str, Material]:
        """
            Returns dict of material_name -> material_data
        """
        materials = {}
        if not self.compiled:
            for dirpath, _, filenames in os.walk("assets/"):
                for filename in filenames:
                    if filename.endswith(".rmat"):
                        name = filename.removesuffix(".rmat")
                        
                        with open(os.path.join(dirpath, filename)) as material_file:
                            material_data = json.load(material_file)
                            shader_path = material_data.get("shader_path", "")
                            texture_path = material_data.get("texture_path", None)
                            properties = material_data.get("properties", {})
                            
                            shader_name = os.path.basename(shader_path).removesuffix(".rshader")
                            shader = shaders.get(shader_name, None)

                            if shader:
                                img = None
                                if texture_path:
                                    img = image.open(texture_path)

                                materials[name] = Material(shader, img.tobytes() if img else None, img.size if img else None, properties)
                            else:
                                Logger("SCENE MANAGEMENT").log_warning(f"Material {name} references unknown shader {shader_name}.")

        else:
            for file in self.pack.files:
                if file.endswith(".rmat"):
                    name = os.path.split(file)[-1].removesuffix(".rmat")
                    material_data = self.pack.get_as_json_dict(file)

                    shader_path: str = material_data.get("shader_path", "")
                    texture_path: str = material_data.get("texture_path", None)
                    properties: dict[str, dict] = material_data.get("properties", {})
                    
                    shader_name = os.path.basename(shader_path).removesuffix(".rshader")
                    shader = shaders.get(shader_name, None)

                    if shader:
                        img = None
                        if texture_path:
                            img = image.open(self.pack.get(texture_path))
                        
                        materials[name] = Material(shader, img.tobytes() if img else None, img.size if img else None, properties)
                    else:
                        Logger("CORE").log_warning(f"Material {name} references unknown shader: {shader_name}.")

                        
        return materials        

    def _instantiate_scene_objects(self, scene_data: dict) -> list[Object]:
        scene_objects = []
            
        game_objects: list[dict] = scene_data["objects"]

        for obj_data in game_objects:
            object_name = obj_data["name"]
            object_transform = Transform(glm.vec3(*obj_data["pos"]), glm.quat(*obj_data["rot"]), glm.vec3(*obj_data["scale"]))
            game_object = Object(object_name, self.materials.get(obj_data["material"], self.materials["base_mat"]), object_transform)
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
        if not self.compiled:
            with open(scene_path) as scene_file:
                scene_data = json.load(scene_file)
        else:
            scene_data = self.pack.get_as_json_dict(scene_path)

        self.game_objects = self._instantiate_scene_objects(scene_data)
        Logger("SCENE MANAGEMENT").log_debug(f"Loaded gameobjects for scene {scene_info.scene_name}|{scene_info.scene_index}")

        # Call load callbacks
        for obj in self.game_objects:
            for script in obj.components:
                script.on_scene_load(scene_info)

    def update_scene(self):
        time = glfw.get_time()
        dt = time - self.last_time
        self.last_time = time
        self.accumulator += dt

        view = glm.lookAt(glm.vec3(0, 0, -5), glm.vec3(0, 0, -5)+glm.vec3(0, 0, 5), glm.vec3(0, 1, 0))
        proj = glm.perspective(glm.radians(45), 800/600, 0.01, 1000)

        for obj in self.game_objects:
            obj.update(dt, view, proj)

        while self.accumulator >= 1/50:
            for obj in self.game_objects:
                obj.fixed_update()
            self.accumulator -= 1/50
