"""
main.py
-------
Punto de entrada principal del Visualizador de Árboles y Recursividad.
Ejecutar desde la raíz del proyecto:

    python main.py
"""

import sys
import os

# Garantizar que la raíz del proyecto esté en el path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from UI.Ui import main

if __name__ == "__main__":
    main()