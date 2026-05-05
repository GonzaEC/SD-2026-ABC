import sys
import os

# Agrega la carpeta raíz del proyecto al inicio del path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)