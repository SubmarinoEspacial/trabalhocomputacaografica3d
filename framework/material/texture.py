"""Material de textura repetível combinado com iluminação Lambert.

Implementação própria apoiada no conceito de texture mapping do capítulo 5,
"Textures", de Stemkoski e Pascale (2022); nenhum código do livro foi copiado.
"""
from core.texture import Texture
from material.lambert import LambertMaterial


class TextureMaterial(LambertMaterial):
    """Carrega textura e usa o mesmo shader iluminado dos materiais sólidos."""

    def __init__(self, lighting, texture, repeatUV=(1.0, 1.0), offsetUV=(0.0, 0.0)):
        if not isinstance(texture, Texture):
            raise TypeError("TextureMaterial requer uma instância de Texture.")
        self.texture = texture
        super().__init__(
            lighting,
            (1.0, 1.0, 1.0),
            texture_id=texture.textureID,
            repeatUV=repeatUV,
            offsetUV=offsetUV,
        )