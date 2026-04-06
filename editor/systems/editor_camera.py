from pyglm import glm
import numpy as np

import glfw

from . import get_modules as modules

Input = None
KeyCodes = None

class editor_camera:
    def __init__(self, input_handler):       
        global KeyCodes, Input
        KeyCodes = modules.KeyCodes
        Input = modules.Input

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
        self.input_handler = input_handler

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

    def get_view_mat(self):
        """ Returns the view matrix calculated using Euler Angles and the LookAt Matrix """
        return glm.lookAt(self.position, self.position + self.front, self.up)
    
    def get_projection_mat(self):
        """ Returns the projection matrix using perspective projection. """
        window_ = glfw.get_current_context()
        aspect_ratio = glfw.get_window_size(window_)[0] / glfw.get_window_size(window_)[1]

        return glm.perspective(glm.radians(self.zoom), aspect_ratio, 0.1, 100.0)
    
    def get_view_pos(self):
        return self.position