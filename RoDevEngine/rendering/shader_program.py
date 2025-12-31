from OpenGL.GL import *
from ..core.logger import Logger
from ..scripts.light import Pointlight, Spotlight
from pyglm import glm
import numpy as np
import ctypes


def is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


# ===============================
# std140 UBO layouts
# ===============================

class PointLightUBO(ctypes.Structure):
    _fields_ = [
        ("position",    ctypes.c_float * 4),  # xyz + intensity
        ("ambient",     ctypes.c_float * 4),
        ("diffuse",     ctypes.c_float * 4),
        ("specular",    ctypes.c_float * 4),
        ("color",       ctypes.c_float * 4),
        ("attenuation", ctypes.c_float * 4),  # constant, linear, quadratic, range
    ]


class SpotLightUBO(ctypes.Structure):
    _fields_ = [
        ("position",    ctypes.c_float * 4),
        ("direction",   ctypes.c_float * 4),
        ("angles",      ctypes.c_float * 4),  # cutOff, outerCutOff
        ("color",       ctypes.c_float * 4),
        ("ambient",     ctypes.c_float * 4),
        ("diffuse",     ctypes.c_float * 4),
        ("specular",    ctypes.c_float * 4),
        ("attenuation", ctypes.c_float * 4),
    ]


# ===============================
# Shader Program
# ===============================

class ShaderProgram:
    MAX_LIGHTS = 64

    def __init__(self, vertex_src, fragment_src):
        self.vertex_src = vertex_src
        self.fragment_src = fragment_src
        self.program_id = self._create_shader_program()

    # -------------------------------------------------
    # Shader compilation / linking
    # -------------------------------------------------

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
            raise RuntimeError(f"Shader linking error:\n{error}")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        # ---------- UBO SETUP ----------
        self._setup_light_ubos(program)

        return program

    def _handle_shader_error(self, shader, stage):
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"{stage} shader compilation error:\n{error}")

    # -------------------------------------------------
    # UBO setup (GL 3.3 compatible)
    # -------------------------------------------------

    def _setup_light_ubos(self, program):
        # ---------- Point Lights ----------
        self.point_light_ubo = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.point_light_ubo)
        glBufferData(
            GL_UNIFORM_BUFFER,
            self.MAX_LIGHTS * ctypes.sizeof(PointLightUBO),
            None,
            GL_DYNAMIC_DRAW
        )

        block_index = glGetUniformBlockIndex(program, "PointLightBlock")
        if block_index != GL_INVALID_INDEX:
            glUniformBlockBinding(program, block_index, 0)
            glBindBufferBase(GL_UNIFORM_BUFFER, 0, self.point_light_ubo)
        else:
            Logger("SHADER").log_warning("PointLightBlock not found in shader.")

        # ---------- Spot Lights ----------
        self.spot_light_ubo = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.spot_light_ubo)
        glBufferData(
            GL_UNIFORM_BUFFER,
            self.MAX_LIGHTS * ctypes.sizeof(SpotLightUBO),
            None,
            GL_DYNAMIC_DRAW
        )

        block_index = glGetUniformBlockIndex(program, "SpotLightBlock")
        if block_index != GL_INVALID_INDEX:
            glUniformBlockBinding(program, block_index, 1)
            glBindBufferBase(GL_UNIFORM_BUFFER, 1, self.spot_light_ubo)
        else:
            Logger("SHADER").log_warning("SpotLightBlock not found in shader.")

        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    # -------------------------------------------------
    # Shader usage helpers
    # -------------------------------------------------

    def use(self):
        glUseProgram(self.program_id)

    def _use_shader(func):
        def wrapper(self, *args, **kwargs):
            self.use()
            return func(self, *args, **kwargs)
        return wrapper

    # -------------------------------------------------
    # Standard uniforms (unchanged)
    # -------------------------------------------------

    @_use_shader
    def set_mat4(self, name: str, matrix: glm.mat4x4):
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(matrix))

    @_use_shader
    def set_mat3(self, name: str, matrix: glm.mat3):
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniformMatrix3fv(loc, 1, GL_FALSE, glm.value_ptr(matrix))

    @_use_shader
    def set_vec3(self, name: str, vector):
        if not isinstance(vector, glm.vec3):
            vector = glm.vec3(*vector)
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniform3fv(loc, 1, glm.value_ptr(vector))

    @_use_shader
    def set_vec2(self, name: str, vector):
        if not isinstance(vector, glm.vec2):
            vector = glm.vec2(*vector)
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniform2fv(loc, 1, glm.value_ptr(vector))

    @_use_shader
    def set_float(self, name: str, value: float):
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniform1f(loc, value)

    @_use_shader
    def set_int(self, name: str, value: int):
        loc = glGetUniformLocation(self.program_id, name)
        if loc != -1:
            glUniform1i(loc, value)
        return loc

    # -------------------------------------------------
    # UBO Light Uploads
    # -------------------------------------------------

    @_use_shader
    def set_point_lights(self, lights: list[Pointlight]):
        glUniform1i(
            glGetUniformLocation(self.program_id, "uNumPointLights"),
            len(lights)
        )

        glBindBuffer(GL_UNIFORM_BUFFER, self.point_light_ubo)

        for i, light in enumerate(lights):
            data = PointLightUBO(
                (light.gameobject.transform.pos.x,
                 light.gameobject.transform.pos.y,
                 light.gameobject.transform.pos.z,
                 light.intensity),

                (*light.ambient, 0.0),
                (*light.diffuse, 0.0),
                (*light.specular, 0.0),
                (*light.color, 0.0),

                (light.constant,
                 light.linear,
                 light.quadratic,
                 light.range)
            )

            glBufferSubData(
                GL_UNIFORM_BUFFER,
                i * ctypes.sizeof(PointLightUBO),
                ctypes.sizeof(PointLightUBO),
                ctypes.byref(data)
            )

        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    @_use_shader
    def set_spot_lights(self, lights: list[Spotlight]):
        glUniform1i(
            glGetUniformLocation(self.program_id, "uNumSpotLights"),
            len(lights)
        )

        glBindBuffer(GL_UNIFORM_BUFFER, self.spot_light_ubo)

        for i, light in enumerate(lights):
            forward = glm.vec3(0, 0, 1)

            direction = glm.normalize(
                light.gameobject.transform.rot * forward
            )

            data = SpotLightUBO(
                (*light.gameobject.transform.pos, light.intensity),
                (*direction, 0.0),

                (glm.cos(light.cutOff),
                glm.cos(light.outerCutOff),
                0.0, 0.0),

                (*light.color, 0.0),
                (*light.ambient, 0.0),
                (*light.diffuse, 0.0),
                (*light.specular, 0.0),

                (light.constant,
                light.linear,
                light.quadratic,
                light.range)
            )

            glBufferSubData(
                GL_UNIFORM_BUFFER,
                i * ctypes.sizeof(SpotLightUBO),
                ctypes.sizeof(SpotLightUBO),
                ctypes.byref(data)
            )

        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    # -------------------------------------------------

    def delete(self):
        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = 0

    def __str__(self):
        return f"ShaderProgram<{self.program_id}>"
