# RoDevEngine
A custom, open-source game engine built using Python, PyOpengl, and GLFW. 

## Recent Updates:
The first version of the editor has released! It took six months, and probably still has a lot of bugs.

## Engine:
### Features:
The engine has a long list of features currently implemented, with more planned as development continues. It currently features easy scene management, game objects with behaviors and names, methods to find game objects with behaviors, custom behaviors, and more.

In the future, even more features will be added, such as different render pipelines (Vulkan and possibly DirectX), easier mesh management, and fully functional rigid bodies.

## Editor:
### How to use:
To run the editor, use Python 3.13 to run Editor/editor.py, and add an argument for the target project's path.

### Editor Windows:
The editor itself consists of many individual panes, or 'windows'. Each window allows the user to access or view different information, to make game development less challenging.

#### Hierarchy:
The Hierarchy is a list of all game objects, and their associated parents. This currently doesn't update mid-test, but that is a planned feature in the future. 

#### Inspector:
The Inspector allows you to view and edit all data for any given object, as well as disable/remove any components attached to it. Like the Hierarchy, this doesn't update during tests, but that feature is planned in the future.

#### Scene View:
The Scene View allows you to view the scene in the same way it would look in a compiled version of the game. This reflects all changes made in the Inspector window.

#### Game View:
The Game View allows you to run/pause/stop the game. This, unlike the Scene View, will cause game updates, which leads to component updates.