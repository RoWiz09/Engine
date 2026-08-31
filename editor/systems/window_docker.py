from __future__ import annotations
from typing import Optional, Literal, Any, TypeAlias

from .editor_windows import *
from . import global_vars as modules

from pyglm import glm
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..editor import Window

from .font import get_size

import OpenGL.GL as gl

Split: TypeAlias = Literal["horizontal", "vertical"]
SplitDirection: TypeAlias = Literal["left", "right", "top", "bottom"]
Child: TypeAlias = Literal["child_a", "child_b"]

@dataclass
class DockNodeEdges:
    left_owner: Optional[DockNode] = None
    right_owner: Optional[DockNode] = None
    top_owner: Optional[DockNode] = None
    bottom_owner: Optional[DockNode] = None

    @property
    def all(self):
        return [self.left_owner, self.top_owner, self.right_owner, self.bottom_owner]

class DockNode:
    CURSOR_AT_FRAME_START = global_vars.current_cursor_type

    def __init__(self, docker: Docker):
        self.split_side: Optional[Split] = None

        self.child_a: Optional[DockNode] = None
        self.child_b: Optional[DockNode] = None
        self.__split_ratio: float = 0.5

        self.parent: Optional[DockNode] = None

        self.est_size: glm.vec2 = glm.vec2(0)
        self.est_pos: glm.vec2 = glm.vec2(0)

        self.windows: dict[EditorUiWindow, Tab] = {}
        self.selected_window = None

        docker.nodes.append(self)
        self.edges = DockNodeEdges()
        self.resizing = False

    @property
    def split_ratio(self):
        return self.__split_ratio

    @split_ratio.setter
    def split_ratio(self, value):
        self.__split_ratio = min(0.95, max(0.05, value))

    @property
    def is_root(self):
        return self.parent is None

    def set_data_from_node(self, node: DockNode):
        if node is self:
            return

        self.split_side = node.split_side
        self.__split_ratio = node.__split_ratio

        self.child_a = node.child_a
        self.child_b = node.child_b

        if self.child_a:
            self.child_a.parent = self
        if self.child_b:
            self.child_b.parent = self

        self.windows = node.windows.copy()

    def split_node(self, node_a: DockNode, node_b: DockNode, split: Split):
        self.child_a = node_a
        self.child_a.parent = self
        self.child_b = node_b
        self.child_b.parent = self

        if split == "horizontal":
            node_a.edges.bottom_owner = self
            node_b.edges.top_owner = self

        elif split == "vertical":
            node_a.edges.right_owner = self
            node_b.edges.left_owner = self

        self.split_side = split

    def is_split(self):
        # RoDev (4/8/26):
        # If one child exists, the other should always exist as well. But just in case someone's gone tampering
        # with the node, check for both.

        return bool(self.child_a or self.child_b)
    
    def get_child(self, node: DockNode) -> Child:
        if node == self.child_a:
            return "child_a"
        
        elif node == self.child_b:
            return "child_b"
        
        else:
            modules.logger("EDITOR").log_warning("Tried to get which child a node was when the node wasn't a child of the parent!")
            return
        
    def render(self, editor: Window) -> bool:
        global Input
        if self.is_split():
            return False
        
        if self.selected_window is None:
            return False
        
        windows = list(self.windows.keys())

        window = windows[self.selected_window]
        window.draw(editor)
        if window.dock_parent is None:
            window.dock_parent = self

        input_ = modules.input_handler()

        mouse_pos = glm.vec2(*input_.mouse_pos)
        pos = self.est_pos + glm.vec2(2, 2)
        for window, button in self.windows.items():
            if button == None:
                size = get_size(window.name, TextStyle.NORMAL, 12)
                tab = Tab(None, size.x + 20, 20, window.name)
                self.windows[window] = tab

                tab.set_selected(windows[self.selected_window] == window)
                tab.draw(editor, pos)
                pos.x += tab.size.x

                if tab.rect.collide_point(mouse_pos) and input_.get_mouse_button_down(modules.mouse_buttons.LEFT):
                    self.selected_window = windows.index(window)

                continue
            
            button.set_selected(windows[self.selected_window] == window)
            button.draw(editor, pos)
            pos.x += button.size.x

            if button.rect.collide_point(mouse_pos):
                global_vars.current_cursor_type = glfw.POINTING_HAND_CURSOR
                if input_.get_mouse_button_down(modules.mouse_buttons.LEFT):
                    self.selected_window = windows.index(window)

        if window.rect.collide_point(mouse_pos):
            return True
        
        return False

    def handle_resize(self, input_handler: global_vars.Input, mouse_buttons: global_vars.MouseButtons):
        if self.is_root:
            return

        mouse_pos = glm.vec2(input_handler.get_cursor_pos())

        x, y = self.est_pos
        w, h = self.est_size

        ew_draggable = False
        ns_draggable = False
        for idx, edge in enumerate(self.edges.all):
            if edge is None:
                continue

            match idx:
                case 0:  # Left
                    x1, y1 = x, y
                    x2, y2 = x + 3, y + h

                case 1:  # Top
                    x1, y1 = x, y
                    x2, y2 = x + w, y + 3

                case 2:  # Right
                    x1, y1 = x + w - 3, y
                    x2, y2 = x + w, y + h
                case 3:  # Bottom
                    x1, y1 = x, y + h - 3
                    x2, y2 = x + w, y + h

                case _:
                    continue

            # Mouse is inside this edge's 3-pixel-wide/tall region
            if x1 <= mouse_pos.x <= x2 and y1 <= mouse_pos.y <= y2:
                ew_draggable = idx == 0 or idx == 2
                ns_draggable = idx == 1 or idx == 3

        cursor = global_vars.current_cursor_type
        if ew_draggable and ns_draggable and cursor != glfw.RESIZE_ALL_CURSOR:
            global_vars.current_cursor_type = glfw.RESIZE_ALL_CURSOR

        elif ew_draggable and cursor != glfw.RESIZE_EW_CURSOR:
            global_vars.current_cursor_type = glfw.RESIZE_EW_CURSOR

        elif ns_draggable and cursor != glfw.RESIZE_NS_CURSOR:
            global_vars.current_cursor_type = glfw.RESIZE_NS_CURSOR

        if (ew_draggable or ns_draggable) and input_handler.get_mouse_button_down(mouse_buttons.LEFT):
            self.resizing = True

        return self.resizing

    def update_size(self, input_handler: global_vars.Input, mouse_buttons: global_vars.MouseButtons):
        if input_handler.get_mouse_button_up(mouse_buttons.LEFT):
            Docker.INST.compute_node(self.parent, global_vars.editor_window)
            self.resizing = False
            return

        source = self.parent.est_pos
        mouse_pos_relative = glm.vec2(input_handler.get_cursor_pos()) - source

        size = self.parent.est_size
        if self.parent.split_side == "vertical":
            split_ratio = mouse_pos_relative.x / size.x
        else:
            split_ratio = mouse_pos_relative.y / size.y

        def within(min_, max_, value):
            return min_ < value < max_

        if not within(self.parent.split_ratio - 0.05, split_ratio, self.parent.split_ratio + 0.05):
            self.parent.split_ratio = split_ratio
            Docker.INST.compute_node(self.parent, global_vars.editor_window)

class Docker:
    INST: Docker = None
    def __init__(self):
        __class__.INST = self
        self.nodes: list[DockNode] = [] 
        self.root = DockNode(self)

        self.current_resize = None

    def get_node_info(self, node: DockNode, editor: Window):
        if not node.parent:
            return glm.vec2(*editor.size()), glm.vec2(0, 0)
        
        parent = node.parent
        child_pos = parent.get_child(node)
        if child_pos == "child_a":
            # Clamp ratio so it can't hide windows
            split_ratio = parent.split_ratio
        else:
            # Ratio should be 1-(clamped ratio)
            split_ratio = 1 - parent.split_ratio
            other_ratio = parent.split_ratio

        base_size = glm.vec2(parent.est_size) # Copy the parent's (estimated) size, and adjust it where needed.
        base_pos = glm.vec2(parent.est_pos) # Copy the parent's (estimated) position, and adjust it when 
        if parent.split_side == "horizontal":
            if child_pos == "child_b":
                base_pos.y += base_size.y * other_ratio

            base_size *= glm.vec2(1, split_ratio)

        elif parent.split_side == "vertical":
            if child_pos == "child_b":
                base_pos.x += base_size.x * other_ratio

            base_size.x *= split_ratio

        else:
            modules.logger("EDITOR").log_error("A node was flagged as invalid, due to it's parent not" + 
                                                        "having a defined split direction!")
            return None
        
        return base_size, base_pos
    
    def set_ratio(self, node: DockNode, ratio: float, editor: Window):
        """
        Sets the split ratio for `node` to `ratio`.

        Args:
            node (DockNode): The node to set the ratio of.
            ratio (float): The split ratio.
            editor (Window): The editor window class instance.
        """
        if not 0 <= ratio <= 1:
            modules.logger("EDITOR").log_warning("A node's split ratio was set to be outside of it's range!")
            return
        
        node.__split_ratio = ratio

        # self.compute_node(node, editor) 

    def compute_node(self, node: DockNode, editor: Window):
        """
        Computes a node tree, starting with `node`. Used when computing a whole tree from `Docker.root` would be inefficient or overkill.

        Args:   
            node (DockNode): The node to start computing at.
            editor (Window): The editor window class instance.
        """

        size, pos = self.get_node_info(node, editor)

        node.est_size = size
        node.est_pos = pos

        cur_nodes = []

        if node.is_split():
            cur_nodes.append(node.child_a)
            cur_nodes.append(node.child_b)

        else:
            for editor_window in node.windows:
                editor_window.resize(*node.est_size)
                editor_window.move(*node.est_pos)

        while len(cur_nodes) > 0:
            node = cur_nodes.pop(0)

            size, pos = self.get_node_info(node, editor)

            node.est_size = size
            node.est_pos = pos

            if node.is_split():
                cur_nodes.append(node.child_a)
                cur_nodes.append(node.child_b)

            else:
                for editor_window in node.windows:
                    editor_window.resize(*node.est_size)
                    editor_window.move(*node.est_pos)

    def compute_layout(self, editor: Window):
        """
        Computes the layout tree from `Docker.root`. Used when computing from a node's tree wouldn't work. 

        Args:
            editor (Window): The editor window class instance.
        """
        self.root.est_size = glm.vec2(editor.size()) - glm.vec2(0, 20)
        self.root.est_pos = glm.vec2(0, 20)

        cur_nodes: list[DockNode] = []
        if self.root.is_split():
            cur_nodes.append(self.root.child_a)
            cur_nodes.append(self.root.child_b)

        else:
            for editor_window in self.root.windows:
                editor_window.resize(*self.root.est_size)
                editor_window.move(*self.root.est_pos)

            return

        while len(cur_nodes) > 0:
            node = cur_nodes.pop(0)

            size, pos = self.get_node_info(node, editor)

            node.est_size = size
            node.est_pos = pos

            if node.is_split():
                cur_nodes.append(node.child_a)
                cur_nodes.append(node.child_b)

            else:
                for editor_window in node.windows:
                    editor_window.resize(*node.est_size)
                    editor_window.move(*node.est_pos)

    def dock(self, node: DockNode, window: EditorUiWindow, split: Optional[SplitDirection] = None):
        """
        Dock a window in `node`.

        Args:
            node (DockNode): The DockNode to dock inside.
            window (EditorUiWindow): The EditorUiWindow instance to dock.
            split (Optional[SplitDirection], optional): The direction of the split. Defaults to None.

        Returns:
            DockNode: the docked node.
        """
        if not node in self.nodes:
            modules.logger("EDITOR").log_warning(f"Tried to dock {window.name} in a non-existent node!")
            return node
        
        # Flag the window as docked.
        setattr(window, "docked", True)
        WindowDrawer.INST.floating_windows.remove(window)
        
        # If there is a split, handle it accordingly
        if split:
            # RoWiz (4/27/26)
            # Completely reworked the split system, as it was bad and didn't work.
            split_dir: Split
            if split in ("top", "bottom"):
                split_dir = "horizontal"
            
            else:
                split_dir = "vertical"

            cur_split = node.split_side
            if cur_split is None:
                child_a = DockNode(self)
                child_b = DockNode(self)

                if node.windows != []:
                    if split in ("top", "left"):
                        child_b.windows = node.windows
                        child_b.selected_window = node.selected_window

                    else:
                        child_a.windows = node.windows
                        child_a.selected_window = node.selected_window
                    node.windows = []

                if split in ("top", "left"):
                    child_a.windows[window] = None
                    child_a.selected_window = len(child_a.windows) - 1

                else:
                    child_b.windows[window] = None
                    child_b.selected_window = len(child_b.windows) - 1

                node.split_node(child_a, child_b, split_dir)

            elif split_dir == cur_split:
                if split in ("top", "left"):
                    node.child_a.windows[window] = None
                    node.child_a.selected_window = len(node.child_a.windows) - 1

                else:
                    node.child_b.windows[window] = None
                    node.child_b.selected_window = len(node.child_b.windows) - 1

            else:
                child_a = DockNode(self)
                child_b = DockNode(self)

                if split in ("top", "left"):
                    child_a.windows[window] = None
                    child_a.selected_window = len(child_a.windows) - 1

                    child_b.set_data_from_node(node)

                else:
                    child_b.windows[window] = None
                    child_b.selected_window = len(child_b.windows) - 1

                    child_a.set_data_from_node(node)

                node.split_node(child_a, child_b, split_dir)

        else:
            # Just dock the window!
            node.windows[window] = None
            node.selected_window = len(node.windows) - 1

        return node

    
    def undock(self, node: DockNode, window: EditorUiWindow):
        """
        Undocks `window` from `node`

        Args:
            node (DockNode): The node to undock from.
            window (EditorUiWindow): The window to undock.
        """
        delattr(window, "docked")
        if not node in self.nodes:
            modules.logger("EDITOR").log_warning(f"Tried to undock {window.name} from a non-existent node!")
            return
        
        if node.is_split():
            modules.logger("EDITOR").log_warning(f"Tried to undock {window.name} from a split node!")
            return
        
        node.windows.pop(window)
        
        # If the user removed the final window, handle accordingly
        if node.windows == {}:
            if parent := node.parent:
                child_me = parent.get_child(node)
                child_not_me = "child_b" if child_me == "child_a" else "child_a"

                setattr(parent, child_me, None)
                other_child: DockNode = getattr(parent, child_not_me)
                parent.set_data_from_node(other_child)
                del other_child

                self.nodes.remove(other_child)

    def update(self, editor: Window):
        """
        Updates dock nodes if `Docker.root` isn't the correct size.

        Args:
            editor (Window): The editor window class instance.
        """
        size = editor.size()
        if self.root.est_size != glm.vec2(size[0], size[1]-20):
            self.compute_layout(editor)

    def draw(self, editor: Window):
        focused = None
        for node in self.nodes:
            focus_state = node.render(editor)
            if focus_state:
                focused = list(node.windows.keys())[node.selected_window]

        return focused

    def validate_resize(self, input_handler: global_vars.Input, mouse_buttons: global_vars.MouseButtons):
        if self.current_resize:
            self.current_resize.update_size(input_handler, mouse_buttons)
            if not self.current_resize.resizing:
                self.current_resize = None

        for node in self.nodes:
            if node.handle_resize(input_handler, mouse_buttons):
                self.current_resize = node
