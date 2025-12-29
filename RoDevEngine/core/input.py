from enum import Enum
import glfw

class MouseButtons(Enum):
    LEFT = glfw.MOUSE_BUTTON_LEFT
    MIDDLE = glfw.MOUSE_BUTTON_MIDDLE
    RIGHT = glfw.MOUSE_BUTTON_RIGHT

class CursorStates(Enum):
    NORMAL = glfw.CURSOR_NORMAL
    HIDDEN = glfw.CURSOR_HIDDEN
    DISABLED = glfw.CURSOR_DISABLED

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

    k_escape = glfw.KEY_ESCAPE    

class Input:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Input, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Input._initialized:
            return  # Prevent reinitialization across scenes or scripts
        self.__keys_pressed_now = set()
        self.__keys_pressed_last = set()

        self.__mouse_pos = (0, 0)
        self.__mouse_buttons_pressed_now = set()
        self.__mouse_buttons_pressed_last = set()
        Input._initialized = True

    def get_inputs(self, window):
        """Polls GLFW and updates key states each frame."""
        self.__keys_pressed_last = self.__keys_pressed_now.copy()
        self.__keys_pressed_now.clear()

        # Collect all pressed keys
        for key in KeyCodes:
            if glfw.get_key(window, key.value) == glfw.PRESS:
                self.__keys_pressed_now.add(key.value)

        self.__mouse_pos = glfw.get_cursor_pos(window)

        self.__mouse_buttons_pressed_last = self.__mouse_buttons_pressed_now.copy()
        self.__mouse_buttons_pressed_now.clear()

        for button in MouseButtons:
            if glfw.get_mouse_button(window, button.value):
                self.__mouse_buttons_pressed_now.add(button.value)

    def get_key_down(self, keycode: KeyCodes) -> bool:
        """True only on the frame the key was pressed."""
        return (
            keycode.value in self.__keys_pressed_now
            and keycode.value not in self.__keys_pressed_last
        )

    def get_key(self, keycode: KeyCodes) -> bool:
        """True while the key is being held."""
        return keycode.value in self.__keys_pressed_now

    def get_key_up(self, keycode: KeyCodes) -> bool:
        """True only on the frame the key was released."""
        return (
            keycode.value in self.__keys_pressed_last
            and keycode.value not in self.__keys_pressed_now
        )
    
    # Mouse
    def get_mouse_button_down(self, mouse_button: MouseButtons) -> bool:
        """True only on the frame the button was pressed."""
        return (
            mouse_button.value in self.__mouse_buttons_pressed_now
            and mouse_button.value not in self.__mouse_buttons_pressed_last
        )

    def get_mouse_button(self, mouse_button: MouseButtons) -> bool:
        """True while the button is being held."""
        return mouse_button.value in self.__mouse_buttons_pressed_now

    def get_mouse_button_up(self, mouse_button: MouseButtons) -> bool:
        """True only on the frame the button was released."""
        return (
            mouse_button.value in self.__mouse_buttons_pressed_last
            and mouse_button.value not in self.__mouse_buttons_pressed_now
        )
    
    def get_cursor_pos(self):
        return self.__mouse_pos
    
    def set_cursor_pos(self, mx: int, my: int):
        glfw.set_cursor_pos(glfw.get_current_context(), mx, my)

    def set_cursor_visibility(self, cursor_state: CursorStates):
        """
        Sets the cursor's visibility
        
        :param cursor_state: The state of the cursor. Hidden hides the cursor, but doesn't recenter it.
        :type cursor_state: CursorStates
        """
        glfw.set_input_mode(glfw.get_current_context(), glfw.CURSOR, cursor_state.value)
    
    @property
    def mouse_pos(self):
        return self.__mouse_pos
    
    @mouse_pos.setter
    def mouse_pos(self, value: tuple[int, int]):
        mx, my = value
        glfw.set_cursor_pos(glfw.get_current_context(), mx, my)
    