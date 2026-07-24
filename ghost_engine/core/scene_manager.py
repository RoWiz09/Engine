from ..rendering.shader_program import ShaderProgram
from ..rendering.material import Material
from .transform import Transform
from .packer import Pack
from ..object import GameObject 
from .input import Input, KeyCodes

from ..scripting.behavior import *

from ..rendering.camera_type import CamType
from ..rendering.light_type import LightType

from ..decorators import deprecated

from pyglm import glm

from PIL import Image as image

from .logger import Logger

from dataclasses import dataclass
from pathlib import Path

import os, json, importlib, glfw, sys
import numpy as np
import inspect

@dataclass(frozen=True)
class SceneInfo:
    scene_name: str
    scene_index: int

class SceneManager:
    BASE_SHADER_VERT = """
    #version 330 core

    layout (location = 0) in vec3 aPos;
    layout (location = 1) in vec3 aNormal;
    layout (location = 2) in vec2 aTexCoord;

    uniform mat4 uModel;
    uniform mat4 uView;
    uniform mat4 uProjection;

    out vec3 vWorldPos;
    out vec3 vNormal;
    out vec2 vTexCoord;

    void main()
    {
        vec4 worldPos = uModel * vec4(aPos, 1.0);
        vWorldPos = worldPos.xyz;

        mat3 normalMatrix = transpose(inverse(mat3(uModel)));
        vNormal = normalize(normalMatrix * aNormal);

        vTexCoord = aTexCoord;
        gl_Position = uProjection * uView * worldPos;
    }"""
    BASE_SHADER_FRAG = """
    #version 330 core

    uniform vec3 uViewPos;
    uniform sampler2D uTexture;
    uniform vec2 uTileData;

    uniform bool uDisableLighting;

    in vec3 vNormal;
    in vec3 vWorldPos;
    in vec2 vTexCoord;

    out vec4 FragColor;

    struct PointLight {
        vec4 position;
        vec4 color;
        float range;
    };

    layout(std140) uniform PointLightBlock {
        PointLight pointLights[64];
    };

    uniform int uNumPointLights;

    struct SpotLight {
        vec4 position; // w: intensity
        vec4 direction;
        vec4 color;
        vec3 config; // x: outer angle, y: inner angle, z: range
    };

    layout(std140) uniform SpotLightBlock {
        SpotLight spotLights[64];
    };

    uniform int uNumSpotLights;

    vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
    {
        float intensity = light.position.w;
        float distance_ = length(light.position.xyz - fragPos) / light.range;
        float rangeFade = pow(1.0 - clamp(distance_, 0.0, 1.0), 3.0);

        float facing = dot(normalize(normal), light.position.xyz - fragPos);
        facing = clamp(facing, 0.0, 1.0);

        vec3 color = light.color.rgb / vec3(255.0) * intensity;
        return (color * rangeFade) * facing;
    }

    vec3 rotateVectorByQuaternion(vec3 v, vec4 q) {
        vec3 temp = cross(q.xyz, v) + q.w * v;
        return v + 2.0 * cross(q.xyz, temp);
    }

    vec3 CalcSpotLight(SpotLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
    {
        vec3 offset_normal = normalize(light.position.xyz - fragPos);
        float theta = dot(normalize(-light.direction.xyz), offset_normal);

        float innerCut = light.config.x;
        float outerCut = light.config.y;
        float epsilon  = innerCut - outerCut;

        float intensity = clamp((theta - outerCut) / max(epsilon, 0.001), 0.0, 1.0) * light.position.w;

        float distance_ = length(light.position.xyz - fragPos) / light.config.z;
        float rangeFade = pow(1.0 - clamp(distance_, 0.0, 1.0), 3.0);

        float facing = dot(normalize(normal), light.position.xyz - fragPos);
        facing = clamp(facing, 0.0, 1.0);

        vec3 color = light.color.rgb / vec3(255.0) * intensity;
        return (color * rangeFade) * facing;
    }

    void main()
    {
        vec3 normal  = normalize(vNormal);
        vec3 viewDir = normalize(uViewPos - vWorldPos);
        vec3 albedo  = texture(uTexture, vTexCoord * uTileData).rgb;

        if (!uDisableLighting) {
            vec3 result = vec3(0.0);
            
            for (int i = 0; i < uNumPointLights; ++i)
                result += CalcPointLight(pointLights[i], normal, vWorldPos, viewDir);

            for (int i = 0; i < uNumSpotLights; ++i)
                result += CalcSpotLight(spotLights[i], normal, vWorldPos, viewDir);

            FragColor = vec4(result * albedo, 1.0);
        }
        else {
            FragColor = vec4(albedo, 1.0);
        }
    }"""

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

        self.game_objects: list[GameObject] = []

        self.last_time = glfw.get_time()
        self.accumulator = 0.0

        self.active_camera: CamType = None

        self.disable_lighting = False

    def load_files(self):
        scenes = {}
        shaders = {}
        mats = set()

        shaders["base_shader"] = ShaderProgram(self.BASE_SHADER_VERT, self.BASE_SHADER_FRAG)
        Material.DEFAULT = Material("base_mat", shaders["base_shader"])

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
                

    def _instantiate_scene_objects(self, scene_data: dict) -> list[GameObject]:
        for lights in LightType.lights.values():
            lights.clear()
            
        scene_objects = []
            
        game_objects: list[dict] = scene_data["objects"]

        def instantiate_scripts(obj: GameObject, scripts: list[dict]):
            obj_scripts = set()
            for comp_data in scripts:
                cls = self.pack.load_behavior(comp_data["module"], comp_data["class"])                
                vars_data: dict = comp_data.get("vars", {})

                if issubclass(cls, Behavior):
                    behavior = cls(obj)
                    for var_name, value in vars_data.items():
                        setattr(behavior, var_name, value)
                    behavior.enabled = comp_data.get("active", True)

                    if not self.active_camera and issubclass(type(behavior), CamType):
                        self.active_camera = behavior

                    obj_scripts.add(behavior)
                    behavior.post_init()
                        
                else:
                    Logger("CORE").log_warning(
                        f"Script {cls.__name__} is not a subclass of Behavior and cannot be applied to {obj.name}!"
                    )   
                
            obj.add_behaviors(*obj_scripts)

        def instantiate_object(obj_data: dict, parent: GameObject = None):
            object_name = obj_data["name"]
            parent_t = None if parent is None else parent.transform
            object_transform = Transform(glm.vec3(*obj_data["pos"]), glm.vec3(*obj_data["rot"]), glm.vec3(*obj_data["scale"]), parent_t)
            game_object = GameObject(object_name, self.materials.get(obj_data["material"], self.materials["base_mat"]), object_transform)
            instantiate_scripts(game_object, obj_data.get("components", []))

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
        for obj in self.game_objects.copy():
            if alert_scripts:
                for script in obj.behaviors:
                    script.on_scene_unload(scene_info)
        
            if not obj.static:
                obj.destroy()
                self.game_objects.remove(obj)


        # Load new scene objects
        scene_data = self.pack.read_json(scene_path)

        self.game_objects = self._instantiate_scene_objects(scene_data)
        Logger("SCENE MANAGEMENT").log_debug(f"Loaded gameobjects for scene {scene_info.scene_name}|{scene_info.scene_index}")

        # Call load callbacks
        if alert_scripts:
            for obj in self.game_objects:
                for script in obj.behaviors:
                    script.on_scene_load(scene_info)

    @deprecated(replacement=GameObject.find_with_behavior)
    def get_objects_with_component(self, component_class) -> list[GameObject]:
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

        def build(node: GameObject):
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

    def save_scene_indices(self):
        for idx, scene in enumerate(self.scenes.values()):
            with open(scene, "r+") as scenefile:
                data = json.load(scenefile)
                data["scene_index"] = idx

                scenefile.seek(0)
                json.dump(data, scenefile, indent=4)
            
