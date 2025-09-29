from OpenGL.GL import *
import numpy as np
import glm

class ShaderProgram:
    def __init__(self, vertex_path, fragment_path):
        self.vertex_path = vertex_path
        self.fragment_path = fragment_path
        self.program_id = self._create_shader_program()

    def _create_shader_program(self):
        with open(self.vertex_path, 'r') as f:
            vertex_src = f.read()
        with open(self.fragment_path, 'r') as f:
            fragment_src = f.read()

        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_src)
        glCompileShader(vertex_shader)
        self._handle_shader_error(vertex_shader)

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_src)
        glCompileShader(fragment_shader)
        self._handle_shader_error(fragment_shader)

        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program).decode()
            raise RuntimeError(f"Shader program linking error: {error}")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        return program
    
    def _handle_shader_error(self, shader):
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"Shader compilation error: {error}")
        
    def use(self):
        glUseProgram(self.program_id)

    def use_shader(func):
        def wrapper(self, *args, **kwargs):
            self.use()
            return func(self, *args, **kwargs)
        return wrapper
    
    @use_shader
    def set_uniform_mat4(self, name, matrix:glm.mat4x4):
        loc = glGetUniformLocation(self.program_id, name)
        glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(matrix))

    @use_shader
    def set_uniform_vec3(self, name, vector:glm.vec3):
        loc = glGetUniformLocation(self.program_id, name)
        glUniform3fv(loc, 1, glm.value_ptr(vector))

    @use_shader
    def set_uniform_float(self, name, value:float):
        loc = glGetUniformLocation(self.program_id, name)
        glUniform1f(loc, value)
    
    @use_shader
    def set_uniform_int(self, name, value:int):
        loc = glGetUniformLocation(self.program_id, name)
        glUniform1i(loc, value)
    
    def delete(self):
        glDeleteProgram(self.program_id)
