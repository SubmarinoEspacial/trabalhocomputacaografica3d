"""Raiz da hierarquia de objetos renderizáveis."""
from framework.core.object3d import Object3D


class Scene(Object3D):
    """Agrupa os objetos de uma cena sem aplicar transformação adicional."""