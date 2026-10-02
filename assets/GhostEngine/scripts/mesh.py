from __future__ import annotations
from ghost_engine.scripting.behavior import Behavior, RenderBehavior, EditorField, RegisterEditorButton

from ghost_engine.datatypes.model_type import Model
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

    mesh_path = EditorField(Model, Model.empty())

    run_in_editor = True

    def __init__(self, gameobject):
        super().__init__(gameobject)

        self.submeshes: dict[MeshBuilder.Mesh, Material] = {}

    def load(self):
        self.mesh_path = Model(self.mesh_path)
        for mesh in ModelLoader.load_obj(self.mesh_path.get_value()):
            self.submeshes[mesh] = Material.DEFAULT

    
    @RegisterEditorButton
    def refresh(self):
        self.submeshes.clear()
        for mesh in ModelLoader.load_obj(self.mesh_path.get_value()):
            self.submeshes[mesh] = Material.DEFAULT
    
    def on_render(self):
        if not self.enabled:
            return
        
        for mesh, mat in self.submeshes.items():
            mat.use()
            mat.shader.set_mat4("uModel", self.gameobject.transform.get_model_matrix())

            mesh.render()
    
    @classmethod
    def create_from_builder(cls, mesh_builder: MeshBuilder, gameobject: GameObject):
        inst = cls(gameobject)
        inst.submeshes[mesh_builder.build_mesh()] = Material.DEFAULT

        del inst.mesh_path

        return inst