from ..rendering.shader_program import ShaderProgram
from ..rendering.material import Material
from .transform import Transform
from .packer import Pack
from ..object import Object 
from .input import Input, KeyCodes

from ..behavior import *

from ..rendering.camera_type import CamType
from ..rendering.light_type import LightType


from pyglm import glm

from PIL import Image as image

from .logger import Logger

from dataclasses import dataclass

import os, json, importlib, glfw, sys
import numpy as np
import inspect

@dataclass(frozen=True)
class SceneInfo:
    scene_name: str
    scene_index: int

def check_iterable(field):
    try: 
        iter(field)
        return True
    except:
        return False

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

        self.materials = {}
        SceneManager._created = True
        
        self.pack = Pack()

        def get_index(scene_data):
            scene_name, scene_path = scene_data
            data = Pack().read_json(scene_path)
            return data["scene_index"]

        self.scenes, self.shaders = self.load_files()
        self.scenes = dict(sorted(self.scenes.items(), key=get_index))

        self.game_objects: list[Object] = []

        self.last_time = glfw.get_time()
        self.accumulator = 0.0

        self.active_camera: CamType = None

        self.disable_lighting = False

    def load_files(self):
        scenes = {}
        shaders = {}
        mats = set()

        for file in self.pack.files:
            if file.name.endswith(".rscene"):
                name = os.path.split(file)[-1].removesuffix(".rscene")

                scenes[name] = file
                
            elif file.name.endswith(".rshader"):
                name = os.path.split(file)[-1].removesuffix(".rshader")

                shader_data: dict = self.pack.read_json(file)
                vertex_path = shader_data.get("VertexShader", "assets\\GhostEngine\\base_shader.vert")
                fragment_path = shader_data.get("FragmentShader", "assets\\GhostEngine\\base_shader.frag")
                
                if vertex_path and fragment_path:
                    shaders[name] = ShaderProgram(self.pack.get_contents(vertex_path), self.pack.get_contents(fragment_path))
                    shaders[name].use()
                else:
                    Logger("SCENE MANAGEMENT").log_warning(f"Shader {name} is missing VertexShader or FragmentShader fields.")

            elif file.name.endswith(".rmat"):
                mats.add(file)

        for file in mats:
            name = os.path.split(file)[-1].removesuffix(".rmat")
            material_data = self.pack.read_json(file)

            shader_path: str = material_data.get("shader_path", "")
            texture_path: str = material_data.get("texture_path", None)
            properties: dict[str, dict] = material_data.get("properties", {})
            
            shader_name = os.path.basename(shader_path).removesuffix(".rshader")
            shader = shaders.get(shader_name, None)

            if shader:
                img = None
                if texture_path:
                    img = image.open(self.pack.get_io(texture_path))
                
                Material(name, shader, img.tobytes() if img else None, img.size if img else None, properties)
            else:
                Logger("CORE").log_warning(f"Material {name} references unknown shader: {shader_name}.") 

        return scenes, shaders
    
    def get_materials(self, shaders:dict[str, ShaderProgram]) -> dict[str, Material]:
        """
            Returns dict of material_name -> Material
        """
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

                            Material(name, shader, img.tobytes() if img else None, img.size if img else None, properties)
                

    def _instantiate_scene_objects(self, scene_data: dict) -> list[Object]:
        for lights in LightType.lights.values():
            lights.clear()
            
        scene_objects = []
            
        game_objects: list[dict] = scene_data["objects"]

        def instantiate_scripts(obj: Object, scripts: list[dict]):
            obj_scripts = set()
            for comp_data in scripts:
                module = importlib.import_module(comp_data["module"])
                cls = getattr(module, comp_data["class"])
                vars_data: dict = comp_data.get("vars", {})

                if issubclass(cls, Behavior):
                    if cls.init_method is None:
                        behavior = cls(obj)
                        for var_name, value in vars_data.items():
                            setattr(behavior, var_name, value)
                        behavior.enabled = comp_data.get("active", True)

                        if not self.active_camera and issubclass(type(behavior), CamType):
                            self.active_camera = behavior

                    else:
                        behavior = cls.init_method(*vars_data, obj)

                        behavior.enabled = comp_data.get("active", True)

                    obj_scripts.add(behavior)
                        
                else:
                    Logger("CORE").log_warning(
                        f"Script {cls.__name__} is not a subclass of Behavior and cannot be applied to {obj.name}!"
                    )   
                
            obj.add_components(*obj_scripts)

        def instantiate_object(obj_data: dict, parent: Object = None):
            object_name = obj_data["name"]
            parent_t = None if parent is None else parent.transform
            object_transform = Transform(glm.vec3(*obj_data["pos"]), glm.vec3(*obj_data["rot"]), glm.vec3(*obj_data["scale"]), parent_t)
            game_object = Object(object_name, self.materials.get(obj_data["material"], self.materials["base_mat"]), object_transform)
            scripts = []

            instantiate_scripts(game_object, obj_data.get("components", []))

            game_object.add_components(*scripts)

            for child in obj_data.get("children", []):
                instantiate_object(child, game_object)

            scene_objects.append(game_object)

        for object in game_objects:
            instantiate_object(object)

        return scene_objects

    def load_scene(self, scene_name: str, alert_scripts: bool = True):
        scene_index = list(self.scenes.keys()).index(scene_name)
        self.load_scene_index(scene_index, alert_scripts)

    def load_scene_index(self, scene_index: int, alert_scripts: bool = True):
        scene_name = list(self.scenes.keys())[scene_index]
        scene_path = self.scenes[scene_name]

        self.cur_scene = scene_name

        # Call unload callbacks on current scene before switching
        scene_info = SceneInfo(scene_name, scene_index)
        if alert_scripts:
            for obj in self.game_objects:
                for script in obj.components:
                    script.on_scene_unload(scene_info)

        # Load new scene objects
        scene_data = self.pack.read_json(scene_path)

        self.game_objects = self._instantiate_scene_objects(scene_data)
        Logger("SCENE MANAGEMENT").log_debug(f"Loaded gameobjects for scene {scene_info.scene_name}|{scene_info.scene_index}")

        # Call load callbacks
        if alert_scripts:
            for obj in self.game_objects:
                for script in obj.components:
                    script.on_scene_load(scene_info)

    def get_objects_with_component(self, component_class) -> list[Object]:
        objects = []
        for object in self.game_objects:
            if not object.enabled:
                continue
            
            if object.get_component(component_class):
                objects.append(object)
        
        return objects

    def get_hierarchy(self):
        tree = {}

        # find roots first
        roots = [obj for obj in self.game_objects if obj.transform.parent is None]

        def build(node: Object):
            children = {}
            for obj in node.children:
                children[obj] = build(obj)
            return children

        for root in roots:
            tree[root] = build(root)

        return {None: tree}

    def render_scene(self, view: glm.mat4x4, proj: glm.mat4x4, view_pos: glm.vec3):
        for shader in self.shaders.values():
            shader.set_point_lights()
            shader.set_spot_lights()

            shader.set_vec3("uViewPos", view_pos)
            shader.set_bool("uDisableLighting", self.disable_lighting)

            shader.set_mat4("uView", view)
            shader.set_mat4("uProjection", proj)

        # Rendering
        for obj in self.game_objects:
            obj.pre_render()

        for obj in self.game_objects:
            obj.render()

        for obj in self.game_objects:
            obj.post_render()

    def update_scene(self):
        time = glfw.get_time()
        dt = time - self.last_time
        self.last_time = time
        self.accumulator += dt
        
        for _, components in Behavior.component_category_registry.items():
            for component in components:
                component.on_frame_start()

        if self.active_camera:
            view = self.active_camera.get_view_mat()
            proj = self.active_camera.get_projection_mat()

            view_pos = self.active_camera.get_view_pos()

        else:
            view = glm.lookAt(glm.vec3(0, 0, 0), glm.vec3(0, 0, 5), glm.vec3(0, 1, 0))
            width, height = glfw.get_window_size(glfw.get_current_context())
            proj = glm.perspective(glm.radians(60), width/height, 0.01, 1000)
            
            view_pos = glm.vec3(0, 0, 0)
        self.render_scene(view, proj, view_pos)

        for obj in self.game_objects:
            obj.update(dt)

        while self.accumulator >= 1/50:
            for obj in self.game_objects:
                obj.fixed_update()
            self.accumulator -= 1/50

        for _, components in Behavior.component_category_registry.items():
            for component in components:
                component.on_frame_end()

    def save(self):        
        scene_path = self.scenes[self.cur_scene]

        hierarchy: dict[Object, dict] = self.get_hierarchy()[None]

        cur_tree = []
        
        # Serialize EditorField data
        def json_serialize(component: Behavior, variable: str):
            field = getattr(component, variable)
            if isinstance(field, (str, int, list, float, bool, dict)):
                return field
            if check_iterable(field):
                return list(field)

        # Turn an object into a JSON dictionary
        def serialize_object(obj: Object, children: dict[Object, dict]):
            base = {
                "name": obj.name,

                "pos": obj.transform.localpos.to_list(),
                "rot": obj.transform.localrot.to_list(),
                "scale": obj.transform.scale.to_list(),

                "material": None,
                "components": [],

                "children": []
            }

            mat_idx = list(self.materials.values()).index(obj.mat)
            material = list(self.materials.keys())[mat_idx]
            base["material"] = material

            for component in obj.components:
                if component.init_method is None:
                    base["components"].append({
                        "module": type(component).__module__,
                        "class": type(component).__name__,
                        "vars": {}
                    })
                    for var, field in vars(type(component)).items():
                        if isinstance(field, EditorField):
                            base["components"][-1]["vars"][var] = json_serialize(component, var)
                else:
                    base["components"].append({
                        "module": type(component).__module__,
                        "class": type(component).__name__,
                        "vars": [
                            *component.init_vars
                        ]
                    })

            if children != {}:
                for child, children in children.items():
                    object_dict = serialize_object(child, children)
                    base["children"].append(object_dict)
                    
            return base
            
        for obj, children in hierarchy.items():
            cur_tree.append(serialize_object(obj, children))

        with open(scene_path, "w") as scene_file:
            json.dump({
                "scene_index": list(self.scenes.keys()).index(self.cur_scene),
                "objects": cur_tree
            }, scene_file)

    def save_scene_indices(self):
        for idx, scene in enumerate(self.scenes.values()):
            with open(scene, "r+") as scenefile:
                data = json.load(scenefile)
                data["scene_index"] = idx

                scenefile.seek(0)
                json.dump(data, scenefile, indent=4)
            
