from OpenGL.GL import *
from RoDevEngine.core.logger import Logger
from pyglm import glm

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
        glUniform3fv(loc, 1, glm.value_ptr(vector))

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
    
    def delete(self):
        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = 0
