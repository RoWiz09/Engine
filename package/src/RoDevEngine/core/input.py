from enum import Enum

import glfw

class KeyCodes(Enum):
    k_A = glfw.KEY_A
    k_B = glfw.KEY_B
    k_C = glfw.KEY_C
    k_D = glfw.KEY_D
    k_E = glfw.KEY_E
    k_F = glfw.KEY_F
    k_G = glfw.KEY_G
    k_H = glfw.KEY_H
    k_I = glfw.KEY_I
    k_J = glfw.KEY_J
    k_K = glfw.KEY_K
    k_L = glfw.KEY_L
    k_M = glfw.KEY_M
    k_N = glfw.KEY_N
    k_O = glfw.KEY_O
    k_P = glfw.KEY_P
    k_Q = glfw.KEY_Q
    k_R = glfw.KEY_R
    k_S = glfw.KEY_S
    k_T = glfw.KEY_T
    k_U = glfw.KEY_U
    k_V = glfw.KEY_V
    k_W = glfw.KEY_W
    k_X = glfw.KEY_X
    k_Y = glfw.KEY_Y
    k_Z = glfw.KEY_Z

    k_space = glfw.KEY_SPACE

    k_0 = glfw.KEY_0
    k_1 = glfw.KEY_1
    k_2 = glfw.KEY_2
    k_3 = glfw.KEY_3
    k_4 = glfw.KEY_4
    k_5 = glfw.KEY_5
    k_6 = glfw.KEY_6
    k_7 = glfw.KEY_7
    k_8 = glfw.KEY_8
    k_9 = glfw.KEY_9

    k_left_control = glfw.KEY_LEFT_CONTROL
    k_right_control = glfw.KEY_RIGHT_CONTROL

    k_left_alt = glfw.KEY_LEFT_ALT
    k_right_alt = glfw.KEY_RIGHT_ALT

    k_left_shift = glfw.KEY_LEFT_SHIFT
    k_right_shift = glfw.KEY_RIGHT_SHIFT

    k_comma = glfw.KEY_COMMA
    k_period = glfw.KEY_PERIOD
    k_slash = glfw.KEY_SLASH
    k_semicolon = glfw.KEY_SEMICOLON
    k_apostrophe = glfw.KEY_APOSTROPHE
    k_left_bracket = glfw.KEY_LEFT_BRACKET
    k_right_bracket = glfw.KEY_RIGHT_BRACKET
    k_backslash = glfw.KEY_BACKSLASH

    k_minus = glfw.KEY_MINUS
    k_plus = glfw.KEY_EQUAL

    k_f1 = glfw.KEY_F1
    k_f2 = glfw.KEY_F2
    k_f3 = glfw.KEY_F3
    k_f4 = glfw.KEY_F4
    k_f5 = glfw.KEY_F5
    k_f6 = glfw.KEY_F6
    k_f7 = glfw.KEY_F7
    k_f8 = glfw.KEY_F8
    k_f9 = glfw.KEY_F9
    k_f10 = glfw.KEY_F10
    k_f11 = glfw.KEY_F11
    k_f12 = glfw.KEY_F12
    k_print_screen = glfw.KEY_PRINT_SCREEN
    k_delete = glfw.KEY_DELETE
    k_backspace = glfw.KEY_BACKSPACE

class Input:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Input, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.__keys_pressed_now = []
        self.__keys_pressed_last = []

    def get_inputs(self, window):
        self.__keys_pressed_last = self.__keys_pressed_now.copy()
        self.__keys_pressed_now.clear()
        for key in KeyCodes:
            if glfw.get_key(window, key.value) == glfw.PRESS:
                self.__keys_pressed_now.append(key.value)

    def get_key_down(self, keycode: KeyCodes):
        return keycode.value in self.__keys_pressed_now and keycode.value not in self.__keys_pressed_last
    
    def get_key(self, keycode: KeyCodes):
        return keycode.value in self.__keys_pressed_now
    
    def get_key_up(self, keycode: KeyCodes):
        return keycode.value in self.__keys_pressed_last and keycode.value not in self.__keys_pressed_now
    