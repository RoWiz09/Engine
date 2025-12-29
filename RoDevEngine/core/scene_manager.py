from ..rendering.shader_program import ShaderProgram
from ..scripts.camera import Camera
from ..rendering.material import Material
from ..scripts.behavior import Behavior
from .transform import Transform
from ..scripts.light import Pointlight, Spotlight
from .packer import Pack
from ..object import Object 
from .input import Input, KeyCodes

from pyglm import glm

from PIL import Image as image

from RoDevEngine.core.logger import Logger

from dataclasses import dataclass

import os, json, importlib, glfw, sys
import numpy as np
import inspect

@dataclass(frozen=True)
class SceneInfo:
    scene_name: str
    scene_index: int

class SceneManager:
    _instance = None
    _created = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SceneManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if SceneManager._created:
            return
        
        self.compiled = not os.path.isfile(".rproj") # If there is a .rproj file, then the project has not been built yet.
        if self.compiled:
            self.pack = Pack()

        self.scenes = self.get_scenes()
        self.shaders = self.get_shaders()
        self.materials = self.get_materials(self.shaders)
        self.game_objects: list[Object] = []

        def get_scripts():
            for dirpath, dirnames, files in os.walk("assets"):
                for filename in files:
                    if filename.endswith(".py"):
                        importlib.import_module(os.path.join(dirpath, filename).replace(os.path.sep, ".").removesuffix(".py"))

        get_scripts()

        self.scripts = {}

        self.last_time = glfw.get_time()
        self.accumulator = 0.0

        self.active_camera: Camera = None

        self.editor = sys.argv[-1] == "--editor"

        if self.editor:
            self.editor_camera_active = False

            class editor_camera:
                def __init__(self):                    
                    self.offset = glm.vec3(0.0, 0.0, 0.0)
                    self.front = glm.vec3(0.0, 0.0, -1.0)
                    self.up = glm.vec3(0.0, 1.0, 0.0)
                    self.right = glm.vec3()
                    self.world_up = glm.vec3(0.0, 1.0, 0.0)

                    self.position = glm.vec3(0.0,0.0,0.0)
                    self.yaw = -90
                    self.pitch = 0
                    self.speed = 5 
                    self.sensitivity = 0.5
                    self.zoom = 45.0
                    self.update_vectors()

                    self.window = glfw.get_current_context()

                def update_vectors(self):
                    front = glm.vec3()
                    front.x = np.cos(glm.radians(self.yaw)) * np.cos(glm.radians(self.pitch))
                    front.y = np.sin(glm.radians(self.pitch))
                    front.z = np.sin(glm.radians(self.yaw)) * np.cos(glm.radians(self.pitch))
                    self.front = glm.normalize(front)
                    self.right = glm.normalize(glm.cross(self.front, self.world_up))
                    self.up = glm.normalize(glm.cross(self.right, self.front))

                def process_keyboard(self, delta_time):
                    velocity = self.speed * delta_time
                    if Input().get_key(KeyCodes.k_W):
                        self.position += self.front * velocity
                    if Input().get_key(KeyCodes.k_S):
                        self.position -= self.front * velocity
                    if Input().get_key(KeyCodes.k_A):
                        self.position -= self.right * velocity
                    if Input().get_key(KeyCodes.k_D):
                        self.position += self.right * velocity

                def process_mouse_movement(self):
                    mx, my = Input().mouse_pos
                    win_width, win_height = glfw.get_window_size(self.window)
                    Input().mouse_pos = (win_width//2, win_height//2)
                    x_offset = mx - win_width//2
                    y_offset = my - win_height//2

                    x_offset *= self.sensitivity
                    y_offset *= self.sensitivity

                    self.yaw += x_offset
                    self.pitch -= y_offset

                    self.pitch = min(max(self.pitch, -89.0), 89.0)

                    self.update_vectors()

                def update(self, deltatime):
                    self.process_keyboard(deltatime)
                    self.process_mouse_movement()

                    self.update_vectors()

                def get_view_matrix(self):
                    """ Returns the view matrix calculated using Euler Angles and the LookAt Matrix """
                    return glm.lookAt(self.position, self.position + self.front, self.up)
                
                def get_projection_matrix(self):
                    """ Returns the projection matrix using perspective projection. """
                    window_ = glfw.get_current_context()
                    aspect_ratio = glfw.get_window_size(window_)[0] / glfw.get_window_size(window_)[1]

                    return glm.perspective(glm.radians(self.zoom), aspect_ratio, 0.1, 100.0)

            self.editor_camera = editor_camera()

        # Load first scene by default
        self.load_scene_index(0)

        SceneManager._created = True

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
            Returns dict of shader_name -> ShaderProgram
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
            Returns dict of material_name -> Material
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
                            if shader_name in shaders.keys():
                                shader = shaders[shader_name]
                            else:
                                Logger("SCENE MANAGEMENT").log_warning(f"Material {name} references unknown shader {shader_name}.")
                                continue

                            img = None
                            if texture_path:
                                img = image.open(texture_path)
                                img = img.transpose(image.FLIP_TOP_BOTTOM)

                            materials[name] = Material(shader, img.tobytes() if img else None, img.size if img else None, properties)
                                
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

        def instantiate_object(obj_data: dict, parent: Object = None):
            object_name = obj_data["name"]
            parent_t = None if parent is None else parent.transform
            object_transform = Transform(glm.vec3(*obj_data["pos"]), glm.vec3(*obj_data["rot"]), glm.vec3(*obj_data["scale"]), parent_t)
            game_object = Object(object_name, self.materials.get(obj_data["material"], self.materials["base_mat"]), object_transform)
            scripts = []

            for comp_data in obj_data.get("components", []):
                module = importlib.import_module(comp_data["module"])
                cls = getattr(module, comp_data["class"])
                vars_data: dict = comp_data.get("vars", {})

                if issubclass(cls, Behavior):
                    if not "init_method" in comp_data.keys():
                        behavior = cls(game_object)
                        for var_name, value in vars_data.items():
                            setattr(behavior, var_name, value)
                        behavior.enabled = comp_data.get("active", True)
                        scripts.append(behavior)

                        if not self.active_camera and isinstance(behavior, Camera) and behavior.enabled:
                            self.active_camera = behavior
                    else:
                        init_method = getattr(cls, comp_data["init_method"])
                        behavior = init_method(*vars_data.values(), game_object)

                        behavior.enabled = comp_data.get("active", True)
                        scripts.append(behavior)
                        
                else:
                    Logger("CORE").log_warning(
                        f"Script {cls.__name__} is not a subclass of Behavior and cannot be applied to {object_name}!"
                    )            

            game_object.add_components(*scripts)

            for child in obj_data.get("children", []):
                instantiate_object(child, game_object)

            scene_objects.append(game_object)

        for object in game_objects:
            instantiate_object(object)

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
                if not self.editor:
                    script.on_scene_unload(scene_info)

        # Load new scene objects
        if not self.compiled:
            with open(scene_path) as scene_file:
                scene_data = json.load(scene_file)
        else:
            scene_data = self.pack.get_as_json_dict(scene_path)

        self.game_objects = self._instantiate_scene_objects(scene_data)
        self.game_objects.reverse()
        Logger("SCENE MANAGEMENT").log_debug(f"Loaded gameobjects for scene {scene_info.scene_name}|{scene_info.scene_index}")

        # Call load callbacks
        for obj in self.game_objects:
            for script in obj.components:
                if not self.editor:
                    script.on_scene_load(scene_info)

    def get_objects_with_component(self, component_class) -> list[Object]:
        objects = []
        for object in self.game_objects:
            if object.get_component(component_class):
                objects.append(object)
        
        return objects

    def get_by_hierarchy(self) -> dict[Object, dict]:
        hierarchy = {None: {}}

        def place_in_tree(obj: Object):
            # Build path to root
            path = []
            current = obj
            while current.transform.parent is not None:
                current = current.transform.parent.gameobject
                path.append(current)

            # Traverse/create tree
            cur_place = hierarchy[None]
            for ancestor in reversed(path):
                cur_place = cur_place.setdefault(ancestor, {})

            # Insert object
            cur_place[obj] = {}

        for obj in self.game_objects:
            place_in_tree(obj)

        return hierarchy

    def update_scene(self):
        time = glfw.get_time()
        dt = time - self.last_time
        self.last_time = time
        self.accumulator += dt

        if self.active_camera and not self.editor:
            camera = self.active_camera
            view = glm.lookAt(
                camera.position_mod + camera.gameobject.transform.pos, 
                camera.position_mod + camera.gameobject.transform.pos + glm.vec3(0, 0, 1) * (camera.rotation_mod * camera.gameobject.transform.rot), 
                glm.vec3(0, 1, 0) * (camera.rotation_mod * camera.gameobject.transform.rot)
            )
            width, height = glfw.get_window_size(glfw.get_current_context())
            proj = glm.perspective(glm.radians(60), width/height, 0.01, 1000)

        elif not self.editor:
            view = glm.lookAt(glm.vec3(0, 0, 0), glm.vec3(0, 0, 5), glm.vec3(0, 1, 0))
            width, height = glfw.get_window_size(glfw.get_current_context())
            proj = glm.perspective(glm.radians(60), width/height, 0.01, 1000)
        
        else:
            if Input().get_key_down(KeyCodes.k_Z):
                self.editor_camera_active = not self.editor_camera_active
            
            if self.editor_camera_active:
                self.editor_camera.update(dt)

            view = self.editor_camera.get_view_matrix()
            proj = self.editor_camera.get_projection_matrix()

        pointlights = []
        spotlights = []
        for light_object in self.get_objects_with_component(Pointlight):
            light: Pointlight = light_object.get_component(Pointlight)
            pointlights.append(light)

        for light_object in self.get_objects_with_component(Spotlight):
            light: Spotlight = light_object.get_component(Spotlight)
            spotlights.append(light)
        
        for shader in self.shaders.values():
            shader.set_point_lights("uPointLights", pointlights)
            shader.set_spot_lights("uSpotLights", spotlights)

        for obj in self.game_objects:
            obj.update(dt, view, proj)

        while self.accumulator >= 1/50:
            for obj in self.game_objects:
                obj.fixed_update()
            self.accumulator -= 1/50
