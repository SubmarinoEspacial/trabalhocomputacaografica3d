"""Inicializa o caminho de importação dos pacotes do framework local."""
from pathlib import Path
import sys


_FRAMEWORK_PATH = str(Path(__file__).resolve().parents[1] / "framework")
if _FRAMEWORK_PATH not in sys.path:
	sys.path.insert(0, _FRAMEWORK_PATH)
