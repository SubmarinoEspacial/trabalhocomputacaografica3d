"""Luz direcional, com direção normalizada e API camelCase compatível."""
import math
from light.light import Light


class DirectionalLight(Light):
    """Luz paralela definida pela direção em que seus raios se propagam."""

    def __init__(self, direction=(0.0, -1.0, 0.0), color=(1.0, 1.0, 1.0), strength=1.0):
        super().__init__(color, strength)
        self.direction = (0.0, -1.0, 0.0)
        self.setDirection(direction)

    def setDirection(self, direction):
        """Define a direção dos raios, normalizando o vetor recebido."""
        comprimento = math.sqrt(sum(componente * componente for componente in direction))
        if comprimento == 0.0:
            raise ValueError("A direção da luz não pode ser nula.")
        self.direction = tuple(componente / comprimento for componente in direction)

    def enableShadows(self, lighting, resolution=2048, orthoSize=26.0, bias=0.0012):
        """Cria câmera ortográfica, DepthMaterial e target como no papel do livro."""
        from light.shadow_map import ShadowMap

        self.shadowMap = ShadowMap(lighting, resolution, orthoSize, bias)
        self.shadowCamera = self.shadowMap.shadowCamera
        self.shadowMaterial = self.shadowMap.depthMaterial
        self.shadowRenderTarget = self.shadowMap.target
        return self.shadowMap