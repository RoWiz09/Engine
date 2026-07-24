from __future__ import annotations
from typing_extensions import overload
from pathlib import Path

import glfw
import os, OpenGL.GL as gl

import importlib
import json

if __name__ == "__main__":
    from systems.editor_camera import editor_camera

    from systems.window_drawer import WindowDrawer, EditorUiWindow
    from systems.window_docker import *
    from systems.editor_windows import *

    from systems.discord_rich_presence import DiscordRichPresence

    from systems.task_scheduler import TaskScheduler

    from systems.build import build_game
    from systems import global_vars

glfw_initalized = False

def glfw_error_handler(e_code:str, desc:str):
    Logger("CORE").log_fatal(f"GLFW Error [{e_code}] : {desc}")

glfw.set_error_callback(glfw_error_handler)

def check_iterable(field):
    try: 
        iter(field)
        return True
    except:
        return False

class Window:
    _instance = None
    _created = False
    def __new__(cls, *args):
        if cls._instance is None:
            cls._instance = super(Window, cls).__new__(cls)

        return cls._instance

    @overload
    def __init__(self, path: str): ...
    @overload
    def __init__(self, path: str, width:int, height:int): ...
    def __init__(self, path: str, width=800, height=600):
        os.chdir(path)
        if self._created:
            return
        
        global glfw_initalized

        if not glfw_initalized:
            glfw.init()

        self.logger = Logger("EDITOR")

        # Set the global_vars.editor_window variable, for easy, global access of this instance.
        global_vars.editor_window = self

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.window = glfw.create_window(width, height, "GhostEngine Editor", None, None)
        glfw.make_context_current(self.window)        

        self.logger.log_debug("GLFW initalized successfully!")

        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        gl.glEnable(gl.GL_STENCIL_TEST)

        self.input_handler = Input()

        self.project_data = None

        compiled = not os.path.isfile(".rproj") # If there is a .rproj file, then the project has not been built yet.
        if compiled:
            self.logger.log_fatal("Unable to edit a compiled game!")

        with open(".rproj") as project_file:
            self.project_data = json.load(project_file)
        os.environ["project"] = self.project_data["name"]
        os.environ["project-path"] = os.getcwd()
        glfw.set_window_title(self.window, "GhostEngine Editor - " + self.project_data["name"])

        # write_packs()

        # RoWiz (5/4/26):
        # Before creating the scene manager, we have to modify the pack class functions.
        # Update - As of 5/7/26, I also add methods to the scene manager for asynchronous scene loading.
        self.setup_pack()
        self.setup_async_loading()

        self.scene_framebuffer = gl.glGenFramebuffers(1)
        self.scene_manager = SceneManager()
        Window._created = True

        self.drawer = WindowDrawer()

        self.docker = Docker()
        scene_viewer = SceneView()
        hierarchy = Hierarchy()
        inspector = Inspector()
        console = ConsoleWindow()
        files = FileViewer()

        self.drawer.add_window_data(scene_viewer)
        self.drawer.add_window_data(hierarchy)
        self.drawer.add_window_data(inspector)
        self.drawer.add_window_data(console)
        self.drawer.add_window_data(files)

        root = self.docker.dock(self.docker.root, scene_viewer, "right")
        self.docker.dock(root.child_a, hierarchy)
        self.docker.set_ratio(root.child_a, 0.15, self)
        self.docker.set_ratio(root, 0.15, self)

        self.docker.dock(root.child_b, inspector, "right")
        self.docker.set_ratio(root.child_b, 0.75, self)

        node = self.docker.dock(root, console, "bottom")
        self.docker.dock(node, files, "bottom")
        self.docker.set_ratio(root, 0.75, self)

        self.docker.compute_layout(self)
        self.editor_cam = editor_camera(self.input_handler)
        self.moving_camera = False

        self.running_game = False
        self.scene_manager.load_scene_index_async(0, alert_scripts = False)
        Hierarchy.rebuild_windows()

        self.setup_root_menu_bar()

        self.last_time = glfw.get_time()

        self.discord_rpc = DiscordRichPresence("1510115212055937075")
        self.discord_rpc.start_handling_activity()

        self.current_primary_popup = None

        self.__task_scheduler__ = TaskScheduler()

    def setup_root_menu_bar(self):
        menu_bar = self.drawer.top_bar
        menu_bar.add_menu("File")

        menu_bar.add_to_menu("File", Button(None, 100, 15, "Save", self.save))
        menu_bar.add_to_menu("File", HorizontalLine(None, width=100))
        menu_bar.add_to_menu("File", Button(None, 100, 15, "Build", build_game))
        menu_bar.add_to_menu("File", HorizontalLine(None, width=100))
        menu_bar.add_to_menu("File", Button(None, 100, 15, "Close", None))

        menu_bar.add_menu("Window")

        for window in EditorUiWindow.window_types:
            if not window.SHOW_IN_WINDOW_MENU:
                continue

            menu_bar.add_to_menu("Window", Button(None, 100, 15, window.name, lambda win=window: self.drawer.add_window_data(win())))

    def should_close(self):
        return glfw.window_should_close(self.window)
    
    def setup_pack(self):
        def pack_init(self: global_vars.Pack):
            self.files_ = []

            assets = Path("assets")
            for dirpath, _, filenames in os.walk(assets):
                dirpath = Path(dirpath)
                if dirpath.parts[-1] == "__pycache__":
                    continue

                for file in filenames:
                    self.files_.append(dirpath / file)

        get_decorator = getattr(global_vars.pack, "_Pack__get_decorator")
        @get_decorator
        def pack_get_contents(inst: global_vars.Pack, path: global_vars.PathLike):
            return path.read_text()
        
        @get_decorator
        def pack_get_raw(inst: global_vars.Pack, path: global_vars.PathLike):
            return path.read_text().encode()
        
        @get_decorator
        def pack_read_json(inst: global_vars.Pack, path: global_vars.PathLike):
            return json.loads(path.read_text())
        
        @property
        def pack_files(inst: global_vars.Pack):
            return inst.files_
        
        def load_behavior(inst: global_vars.Pack, module: str, behavior_class: str):
            import importlib
            module = importlib.import_module(module)
            return getattr(module, behavior_class)
        
        setattr(global_vars.pack, "__init__", pack_init)
        setattr(global_vars.pack, "get_contents", pack_get_contents)
        setattr(global_vars.pack, "get_raw", pack_get_raw)
        setattr(global_vars.pack, "read_json", pack_read_json)
        setattr(global_vars.pack, "files", pack_files)
        setattr(global_vars.pack, "load_behavior", load_behavior)

    def setup_async_loading(self):
        def load_scene_index_async(self: global_vars.SceneManager, scene_index: int, alert_scripts: bool = True):
            Logger("SCENE MANAGEMENT").log_debug(f"Loading scene {scene_index} asynchronously")
            async def load(scene_index, alert_scripts):
                self.load_scene_index(scene_index, alert_scripts)

            asyncio.run(load(scene_index, alert_scripts))

        def load_scene_async(self: global_vars.SceneManager, scene_name: str, alert_scripts: bool = True):
            Logger("SCENE MANAGEMENT").log_debug(f"Loading scene {scene_name} asynchronously")
            async def load(scene_name, alert_scripts):
                self.load_scene(scene_name, alert_scripts)

            asyncio.run(load(scene_name, alert_scripts))

        setattr(global_vars.scene_manager, "load_scene_index_async", load_scene_index_async)
        setattr(global_vars.scene_manager, "load_scene_async", load_scene_async)

    def render_scene(self, frame_buffer = None):
        frame_buffer = frame_buffer if frame_buffer else self.scene_framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frame_buffer)
        gl.glEnable(gl.GL_DEPTH_TEST)

        gl.glClearColor(0.25, 0.25, 1, 1)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)

        self.scene_manager.render_scene(
            self.editor_cam.get_view_mat(), 
            self.editor_cam.get_projection_mat(), 
            self.editor_cam.get_view_pos()
        )

        if frame_buffer != 0:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glDisable(gl.GL_DEPTH_TEST)

    def update(self):
        if glfw.get_window_attrib(self.window, glfw.ICONIFIED) != 0:
            return
        
        cur_time = glfw.get_time()
        dt = cur_time - self.last_time
        self.last_time = cur_time

        glfw.poll_events()
        self.input_handler.get_inputs(self.window)

        if self.input_handler.get_key_down(KeyCodes.k_Z) and isinstance(self.drawer.focused_window, SceneView):
            self.moving_camera = not self.moving_camera

        # Set up for a new frame
        width, height = self.size()
        gl.glViewport(0, 0, width, height)

        if self.moving_camera:
            self.editor_cam.update(dt)

        # Rendering
        self.docker.update(self)
        self.__render_editor_ui()

        glfw.swap_buffers(self.window)

        self.__task_scheduler__.update_tasks()

    def __render_editor_ui(self):
        self.drawer.render(self)
        if not self.moving_camera:
            self.drawer.handle_input(KeyCodes, MouseButtons, self.input_handler)

    def size(self):
        return glfw.get_window_size(self.window)

    def terminate(self):
        glfw.terminate()

    def save(self):
        scene_manager = self.scene_manager
        
        scene_path = scene_manager.scenes[scene_manager.cur_scene]
        hierarchy: dict[GameObject, dict] = scene_manager.get_hierarchy()[None]

        cur_tree = []
        
        # Serialize EditorField data
        def json_serialize(component: global_vars.Behavior, variable: str):
            field = getattr(component, variable)
            if isinstance(field, (str, int, list, float, bool, dict)):
                return field
            
            if issubclass(type(field), global_vars.engine_data_type):
                return field.get_value()
            
            if check_iterable(field):
                return list(field)

        # Turn an object into a JSON dictionary
        def serialize_object(obj: GameObject, children: dict[GameObject, dict]):
            base = {
                "name": obj.name,

                "pos": obj.transform.localpos.to_list(),
                "rot": obj.transform.localrot.to_list(),
                "scale": obj.transform.scale.to_list(),

                "material": None,
                "components": [],

                "children": []
            }

            mat_idx = list(scene_manager.materials.values()).index(obj.mat)
            material = list(scene_manager.materials.keys())[mat_idx]
            base["material"] = material

            for component in obj.behaviors:
                base["components"].append({
                    "module": type(component).__module__,
                    "class": type(component).__name__,
                    "vars": {}
                })
                for var, field in vars(type(component)).items():
                    if isinstance(field, global_vars.editor_field):
                        base["components"][-1]["vars"][var] = json_serialize(component, var)

            if children != {}:
                for child, children in children.items():
                    object_dict = serialize_object(child, children)
                    base["children"].append(object_dict)
                    
            return base
            
        for obj, children in hierarchy.items():
            cur_tree.append(serialize_object(obj, children))

        with open(scene_path, "w") as scene_file:
            json.dump({
                "scene_index": list(scene_manager.scenes.keys()).index(scene_manager.cur_scene),
                "objects": cur_tree
            }, scene_file)

def get_path(location: str):
    if not location.endswith(".rproj") or not os.path.exists(location):
        raise ValueError("Executable argument project-path is" +
                         " pointing to an invalid or missing project!")
    
    return os.path.split(location)[0]

if __name__ == "__main__":
    global_vars.parse_args()
    base_path = get_path(global_vars.ARGS.project)
    os.chdir(base_path)
    Logger, SceneManager, Input = global_vars.get_modules(base_path)
    global_vars.logger_module.configure_loggers(log_to_console = True, log_level = global_vars.logger_module.LoggingLevels.DEBUG)
    KeyCodes, MouseButtons = global_vars.key_codes, global_vars.mouse_buttons

    global_vars.MAIN_PROC = True
    
    getattr(sys.modules["ghost_engine.core.logger"], "setup")()

    window = Window(base_path)
    while not window.should_close():
        window.update()

    window.terminate()
