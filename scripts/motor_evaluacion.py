"""Entrada compatible para la herramienta actual; requiere el entorno del proyecto."""
import sys
from pdns_lab.cli import main

if __name__ == "__main__":
    main(["run", *sys.argv[1:]])
