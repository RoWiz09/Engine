from PyInstaller.utils.hooks import collect_dynamic_libs
import PyInstaller.__main__
import os

glfw = collect_dynamic_libs("glfw")
print(*[f"{lib}" for lib in glfw])
script_name = "editor.py"
app_name = 'Editor'

PyInstaller.__main__.run([
    f'--name={app_name}',
    '--windowed',
    # '--icon=app_icon.ico',
    *[f'--add-binary={lib[0]};{lib[1]}' for lib in glfw],
    os.path.join(os.getcwd(), script_name)
])