from __future__ import annotations
from ghost_engine.scripting.behavior import Behavior, RenderBehavior, EditorField, InitMethod, register_editor_button

from ghost_engine.core.model_loader import ModelLoader
from ghost_engine.mesh_builder import MeshBuilder

from ghost_engine.core.packer import Pack

from ghost_engine.object import GameObject
from ghost_engine.rendering.material import Material

from OpenGL import GL
import numpy as np
import hashlib

import os

class Mesh(Behavior, RenderBehavior):
    category = "Rendering"

    # Class-level registry for shared mesh data
    _mesh_registry = {}

    mesh_path = EditorField(str, "")

    run_in_editor = True

    def __init__(self, gameobject):
        super().__init__(gameobject)

        self.submeshes: dict[MeshBuilder.Mesh, Material] = {}

    @InitMethod
    def create_from_obj(cls: type[Mesh], file_path: str, game_object: GameObject):
        inst = cls(game_object)
        for mesh in ModelLoader.load_obj(file_path):
            inst.submeshes[mesh] = Material.DEFAULT

        return inst
    
    @register_editor_button
    def refresh(self):
        self.reload_obj(self.mesh_path)

    @create_from_obj.refresh_vars
    def reload_obj(self, file_path: str):
        self.submeshes = ModelLoader.load_obj(file_path)
    
    def on_render(self):
        if not self.enabled:
            return
        
        for mesh, mat in self.submeshes.items():
            mat.use()
            mat.shader.set_mat4("uModel", self.gameobject.transform.get_model_matrix())

            mesh.render()
    
    @classmethod
    def create_from_builder(cls, mesh_builder: MeshBuilder):
        mesh_builder