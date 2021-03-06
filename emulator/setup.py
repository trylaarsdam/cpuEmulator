"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = ['../controlmap.json','../assembler/assembled.o','../assembler/code.asm','../assembler/ram.o','../microassembler/microcode.o']
OPTIONS = {}

setup(
    name='CPU Emulator',
    version='0.0.4-alpha',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
