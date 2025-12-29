from OpenGL.GL import *
from ..core.logger import Logger
from ..scripts.light import Pointlight, Spotlight
from pyglm import glm
import numpy as np

def is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False

class ShaderProgram:
    def __init__(self, vertex_src, fragment_src):
        self.vertex_src = vertex_src
        self.fragment_src = fragment_src
        self.program_id = self._create_shader_program()

    def _create_shader_program(self):
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, self.vertex_src)
        glCompileShader(vertex_shader)
        self._handle_shader_error(vertex_shader, "VERTEX")

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, self.fragment_src)
        glCompileShader(fragment_shader)
        self._handle_shader_error(fragment_shader, "FRAGMENT")

        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)

        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program).decode()
            raise RuntimeError(f"Shader linking error: {error}")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        return program
    
    def _handle_shader_error(self, shader, stage):
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"{stage} shader compilation error:\n{error}")
        
    def use(self):
        glUseProgram(self.program_id)

    # decorator
    def _use_shader(func):
        def wrapper(self, *args, **kwargs):
            self.use()
            return func(self, *args, **kwargs)
        return wrapper
    
    @_use_shader
    def set_mat4(self, name:str, matrix:glm.mat4x4):
        loc = glGetUniformLocation(self.program_id, name)
        if loc == -1:
            Logger("SHADER").log_warning(f"Uniform '{name}' not found in shader.")
            return
        glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(matrix))

    @_use_shader
    def set_mat3(self, name, matrix: glm.mat3):
        loc = glGetUniformLocation(self.program_id, name)
        if not isinstance(matrix, glm.mat3):
            Logger("SHADER").log_warning(f"'{type(matrix).__name__}' is not a glm.mat3.")
            return
        if loc == -1:
            Logger("SHADER").log_warning(f"Uniform '{name}' not found.")
            return
        glUniformMatrix3fv(loc, 1, GL_FALSE, glm.value_ptr(matrix))

    @_use_shader
    def set_vec3(self, name:str, vector):
        if isinstance(vector, glm.vec3):
            pass
        elif is_iterable(vector) and len(vector) == 3:
            vector = glm.vec3(*vector)
        else:
            Logger("SHADER").log_error(f"{type(vector).__name__} is not valid for glm.vec3!")
            return

        loc = glGetUniformLocation(self.program_id, name)
        if loc == -1:
            Logger("SHADER").log_warning(f"Uniform '{name}' not found in shader.")
            return
        
        Logger("SHADER").log_debug(f"Sending {vector} to shader at {name} with loc of {loc}")
        glUniform3fv(loc, 1, glm.value_ptr(vector))

        buffer = np.zeros(3, dtype=np.float32)
        glGetUniformfv(self.program_id, loc, buffer)
        Logger("SHADER").log_debug(f"{buffer}")

    @_use_shader
    def set_vec2(self, name:str, vector):
        if isinstance(vector, glm.vec2):
            pass
        elif is_iterable(vector) and len(vector) == 2:
            vector = glm.vec2(*vector)
        else:
            Logger("SHADER").log_error(f"{type(vector).__name__} is not valid for glm.vec2!")
            return

        loc = glGetUniformLocation(self.program_id, name)
        if loc == -1:
            Logger("SHADER").log_warning(f"Uniform '{name}' not found in shader.")
            return
        
        Logger("SHADER").log_debug(f"Sending {vector} to shader at {name} with loc of {loc}")
        glUniform2fv(loc, 1, glm.value_ptr(vector))

        buffer = np.zeros(2, dtype=np.float32)
        glGetUniformfv(self.program_id, loc, buffer)
        Logger("SHADER").log_debug(f"{buffer}")

    @_use_shader
    def set_float(self, name:str, value:float):
        loc = glGetUniformLocation(self.program_id, name)
        if loc == -1:
            Logger("SHADER").log_warning(f"Uniform '{name}' not found in shader.")
            return
        glUniform1f(loc, value)
    
    @_use_shader
    def set_int(self, name:str, value:int):
        loc = glGetUniformLocation(self.program_id, name)
        if loc == -1:
            Logger("SHADER").log_warning(f"Uniform '{name}' not found in shader.")
            return
        glUniform1i(loc, value)
    
        return loc
    def delete(self):
        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = 0

    def __str__(self):
        return f"ShaderProgram<{self.program_id}>"
    
    @_use_shader
    def set_directional_light(self, name: str, light: Spotlight):
        """
            Sets the active directional light in the scene.\n
            You can only have ONE directional light.
            Args:
                name (str): The name of the light uniform
                light (light): The light data.
        """
        
        self.set_vec3(f"{name}.direction", light.direction)
        self.set_vec3(f"{name}.ambient",   light.ambient)
        self.set_vec3(f"{name}.diffuse",   light.diffuse)
        self.set_vec3(f"{name}.specular",  light.specular)

    @_use_shader
    def __set_point_light(self, base_name: str, index: int, light: Pointlight):
        prefix = f"{base_name}[{index}]"

        self.set_vec3(f"{prefix}.position",  light.gameobject.transform.pos)
        self.set_vec3(f"{prefix}.ambient",   light.ambient)
        self.set_vec3(f"{prefix}.diffuse",   light.diffuse)
        self.set_vec3(f"{prefix}.specular",  light.specular)

        self.set_vec3(f"{prefix}.color", light.color)

        self.set_float(f"{prefix}.constant",  light.constant)
        self.set_float(f"{prefix}.linear",    light.linear)
        self.set_float(f"{prefix}.quadratic", light.quadratic)

        self.set_int(f"{prefix}.intensity", light.intensity)

    @_use_shader
    def set_point_lights(self, uniform_name: str, lights: list[Pointlight]):
        """
            Sets all point lights in the scene.
            Args:
                uniform_name (str): The name of the light uniform.
                lights (list[light]): The active lights in the scene. \
                    These all need to be point lights.
        """
        l = self.set_int("uNumPointLights", len(lights))

        for i, light in enumerate(lights):
            try:            
                Logger("SHADER").log_debug("Sending light data")
                Logger("SHADER").log_debug(f"Light Data: {light.ambient, light.diffuse, light.specular}")
                self.__set_point_light(uniform_name, i, light)
            except:
                Logger("SHADER").log_error("A non-point light is trying to be used as a point light!")
                continue

        buffer = np.zeros(1, dtype=np.float32)
        glGetUniformfv(self.program_id, l, buffer)
        Logger("SHADER").log_debug(f"Number of Point Lights: {buffer}")

    @_use_shader
    def __set_spot_light(self, base_name: str, index: int, light: Spotlight):
        prefix = f"{base_name}[{index}]"

        # Position + direction
        self.set_vec3(f"{prefix}.position",  light.gameobject.transform.pos)
        forward = glm.vec3(0, 0, 1)
        dir = glm.normalize(light.gameobject.transform.rot * glm.quat(glm.radians(light.direction)) * forward)

        self.set_vec3(f"{prefix}.direction", dir)

        # Colors
        self.set_vec3(f"{prefix}.ambient",   light.ambient)
        self.set_vec3(f"{prefix}.diffuse",   light.diffuse)
        self.set_vec3(f"{prefix}.specular",  light.specular)
        self.set_vec3(f"{prefix}.color", light.color)

        # Angles
        self.set_float(f"{prefix}.cutOff",       glm.cos(light.cutOff))
        self.set_float(f"{prefix}.outerCutOff",  glm.cos(light.outerCutOff))
        self.set_float(f"{prefix}.range", light.range)

        # Attenuation
        self.set_float(f"{prefix}.constant",  light.constant)
        self.set_float(f"{prefix}.linear",    light.linear)
        self.set_float(f"{prefix}.quadratic", light.quadratic)

        # Intensity
        self.set_float(f"{prefix}.intensity", light.intensity)

    @_use_shader
    def set_spot_lights(self, uniform_name: str, lights: list[Spotlight]):
        """
            Sets all spot lights in the scene.
            Args:
                uniform_name (str): The base name of the spotlight array (e.g. "uSpotLights")
                lights (list[Spotlight]): Active spotlights in scene.
        """
        # Set count
        loc = self.set_int("uNumSpotLights", len(lights))

        # Push each spotlight
        for i, light in enumerate(lights):
            try:
                self.__set_spot_light(uniform_name, i, light)
            except Exception as e:
                Logger("SHADER").log_error(f"Invalid spotlight at index {i}: {e}")
                continue

        # Debug readback
        buffer = np.zeros(1, dtype=np.float32)
        glGetUniformfv(self.program_id, loc, buffer)
        Logger("SHADER").log_debug(f"Number of Spot Lights: {buffer}")
