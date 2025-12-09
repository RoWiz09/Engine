from core.packer import Pack

import os

def build_game():
    print("Building the game...")

    # # Build the executable using PyInstaller
    # try:
    #     if os.system("py -m PyInstaller main.py") != 0:
    #         print("Failed to build the executable.")
    # except Exception as e:
    #     print(f"Error during build: {e}")

    print("Writing asset packs...")

    # Pack the game assets
    Pack.write_packs()

    print("Game built successfully!")

if __name__ == "__main__":
    build_game()