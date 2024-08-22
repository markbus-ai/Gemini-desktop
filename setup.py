import sys
from cx_Freeze import setup, Executable

# Dependencias
build_exe_options = {
    "packages": [
        "os",
        "customtkinter",
        "google.generativeai",
        "datetime",
        "random",
        "webbrowser",
        "PyPDF2",
        "json",
        "matplotlib",
        "pygments",
        "threading",
        "time",
        "pyperclip",
    ],
    "excludes": [],
    "include_files": ["api.txt", "prompt.txt"],
}

# Ejecutable
base = "Win32GUI"

setup(
    name="ChatBot AI",
    version="1.0",
    description="ChatBot AI con interfaz gráfica",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="icon.ico")],
)
