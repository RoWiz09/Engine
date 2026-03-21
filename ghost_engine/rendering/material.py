from __future__ import annotations
from typing import Optional

import OpenGL.GL as gl
import PIL.Image as image

from ..core.logger import Logger
from ..rendering.shader_program import ShaderProgram

class register_mat:
    def __init__(self, cls):
        self.cls = cls

    def __call__(self, name, *args, **kwds):
        mat_cls = self.cls(*args)

        from ..core.scene_manager import SceneManager
        SceneManager().materials[name] = mat_cls

        return mat_cls

@register_mat
class Material:
    def __init__(self, shader: ShaderProgram, texture_data: Optional[bytes], texture_size: Optional[tuple[int, int]] = None, properties: Optional[dict] = None):
        self.shader = shader
        self.properties = properties if properties else {}

        self.texture = gl.glGenTextures(1)
        if not texture_data:
            # Create a default white texture
            white_pixel = [255, 255, 255, 255]
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, 1, 1, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, bytes(white_pixel))
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        else:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, *texture_size, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data)
            gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        Logger("CORE").log_debug(f"Material created with shader: {shader}, properties: {self.properties}")

    def use(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        
        self.shader.use()
        for property, value in self.properties.items():
            if isinstance(value, dict) and "type" in value and "value" in value:
                if value["type"] == "vec3":
                    self.shader.set_vec3(property, tuple(value["value"]))
                elif value["type"] == "float":
                    self.shader.set_float(property, float(value["value"]))
                elif value["type"] == "vec2":
                    self.shader.set_vec2(property, tuple(value["value"]))

            else:
                Logger("CORE").log_warning(f"Property {property} has an invalid format: {value}")