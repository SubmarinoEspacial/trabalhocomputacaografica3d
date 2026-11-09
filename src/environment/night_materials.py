"""Ajustes noturnos de exposição e neblina sem alterar o framework.

O shader Lambert compartilhado recebe uniforms extras depois que o
``LightingContext`` envia os valores tradicionais. Assim, todos os materiais do
projeto continuam usando a mesma iluminação direcional e o mesmo shadow map.
"""
from pathlib import Path

from OpenGL.GL import (
    GL_TEXTURE0,
    GL_TEXTURE2,
    GL_TEXTURE_2D,
    glActiveTexture,
    glBindTexture,
    glGetUniformLocation,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniform4f,
)

from core.texture import Texture
from light.shadow_map import _camera_view_matrix
from material.lambert import LambertMaterial, LightingContext
from material.water import WaterMaterial
from src import config as C


_UNIFORMS_NOTURNOS = ("u_exposure", "u_gamma", "u_fog_density")
_UNIFORMS_AGUA = (
    "u_wave3", "u_wave_speed3", "u_wave4", "u_wave_speed4",
    "u_foam_texture", "u_foam_scale", "u_foam_strength", "u_specular_strength",
)
_LUZ_APAGADA = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0)


def _localizacoes_luzes_pontuais(program):
    """Consulta os uniforms dos quatro slots de luzes pontuais."""
    return {
        "count": glGetUniformLocation(program, "u_point_light_count"),
        "position": tuple(
            glGetUniformLocation(program, f"u_point_light_position_eye[{i}]")
            for i in range(C.MAX_POINT_LIGHTS)
        ),
        "color": tuple(
            glGetUniformLocation(program, f"u_point_light_color[{i}]")
            for i in range(C.MAX_POINT_LIGHTS)
        ),
        "range": tuple(
            glGetUniformLocation(program, f"u_point_light_range[{i}]")
            for i in range(C.MAX_POINT_LIGHTS)
        ),
    }


def _enviar_luzes_pontuais(uniforms, luzes_olho, quantidade):
    """Envia apenas as luzes ativas e mantém os slots restantes apagados."""
    if uniforms["count"] != -1:
        glUniform1i(uniforms["count"], int(quantidade))
    for index in range(C.MAX_POINT_LIGHTS):
        posicao, cor, alcance = (
            luzes_olho[index] if index < quantidade else _LUZ_APAGADA
        )
        if uniforms["position"][index] != -1:
            glUniform3f(uniforms["position"][index], *posicao)
        if uniforms["color"][index] != -1:
            glUniform3f(uniforms["color"][index], *cor)
        if uniforms["range"][index] != -1:
            glUniform1f(uniforms["range"][index], alcance)


class NoiteLightingContext(LightingContext):
    """Contexto de iluminação com exposição, gamma e neblina exponencial."""

    def __init__(
        self,
        light,
        ambientLight=None,
        fogColor=C.FOG_COLOR,
        fogStart=C.FOG_START,
        fogEnd=C.FOG_END,
        fogDensity=C.FOG_DENSITY,
        exposure=C.EXPOSURE,
        gamma=C.GAMMA,
    ):
        super().__init__(
            light,
            ambientLight,
            fogColor=fogColor,
            fogStart=fogStart,
            fogEnd=fogEnd,
        )
        self.fogDensity = float(fogDensity)
        self.exposure = float(exposure)
        self.gamma = float(gamma)
        self.nightUniforms = {
            nome: glGetUniformLocation(self.program, nome)
            for nome in _UNIFORMS_NOTURNOS
        }
        self.pointLightUniforms = _localizacoes_luzes_pontuais(self.program)
        self.point_light_count = 0
        self._point_lights_eye = tuple(
            _LUZ_APAGADA for _ in range(C.MAX_POINT_LIGHTS)
        )

    @property
    def point_lights_eye(self):
        """Slots já convertidos para o espaço do olho, prontos para a água."""
        return self._point_lights_eye

    def set_point_lights(self, lights, camera):
        """Converte as luzes do mundo para o espaço do olho da câmera."""
        view_matrix = _camera_view_matrix(camera)
        ativas = [
            luz for luz in lights
            if luz.enabled and luz.strength > 0.0
        ][:C.MAX_POINT_LIGHTS]
        self.point_light_count = len(ativas)
        slots = []
        for luz in ativas:
            posicao = luz.eye_position(view_matrix)
            slots.append((
                (float(posicao[0]), float(posicao[1]), float(posicao[2])),
                luz.eye_color(),
                float(luz.eye_range()),
            ))
        while len(slots) < C.MAX_POINT_LIGHTS:
            slots.append(_LUZ_APAGADA)
        self._point_lights_eye = tuple(slots)

    setPointLights = set_point_lights

    def _enviar_ajustes_noturnos(self):
        """Envia os uniforms extras após o programa Lambert já estar ativo."""
        self._enviar_uniform(self.nightUniforms["u_exposure"], self.exposure)
        self._enviar_uniform(self.nightUniforms["u_gamma"], self.gamma)
        self._enviar_uniform(self.nightUniforms["u_fog_density"], self.fogDensity)

    @staticmethod
    def _enviar_uniform(localizacao, valor):
        # glGetUniformLocation devolve -1 quando o driver remove um uniform não usado.
        if localizacao != -1:
            glUniform1f(localizacao, valor)

    def activate(self):
        """Reaproveita a ativação base e complementa a atmosfera noturna."""
        super().activate()
        self._enviar_ajustes_noturnos()
        _enviar_luzes_pontuais(
            self.pointLightUniforms,
            self._point_lights_eye,
            self.point_light_count,
        )


class TexturedPhongMaterial(LambertMaterial):
    """Combina uma textura repetível com o especular do material Phong."""

    def __init__(
        self,
        lighting,
        texture,
        color=(1.0, 1.0, 1.0),
        repeatUV=(1.0, 1.0),
        offsetUV=(0.0, 0.0),
        specular=(0.32, 0.32, 0.32),
        shininess=36.0,
        alpha=1.0,
        emissive=(0.0, 0.0, 0.0),
        emissiveStrength=1.0,
        transparent=False,
        casts_shadow=True,
    ):
        if not isinstance(texture, Texture):
            raise TypeError("TexturedPhongMaterial requer uma instância de Texture.")
        self.texture = texture
        super().__init__(
            lighting,
            color,
            texture_id=texture.textureID,
            alpha=alpha,
            emissive=emissive,
            emissiveStrength=emissiveStrength,
            repeatUV=repeatUV,
            offsetUV=offsetUV,
            specular=specular,
            shininess=shininess,
            transparent=transparent,
            casts_shadow=casts_shadow,
        )


class NoiteWaterMaterial(WaterMaterial):
    """Água que compartilha exposição/gamma/neblina com os demais materiais."""

    def __init__(self, lighting, fogDensity=C.FOG_DENSITY, exposure=C.EXPOSURE, gamma=C.GAMMA):
        super().__init__(lighting)
        self.fogDensity = float(fogDensity)
        self.exposure = float(exposure)
        self.gamma = float(gamma)
        self.nightUniforms = {
            nome: glGetUniformLocation(self.program, nome)
            for nome in _UNIFORMS_NOTURNOS
        }
        self.waterUniforms = {
            nome: glGetUniformLocation(self.program, nome)
            for nome in _UNIFORMS_AGUA
        }
        self.pointLightUniforms = _localizacoes_luzes_pontuais(self.program)
        raiz = Path(__file__).resolve().parents[2]
        self.foamTexture = Texture(
            raiz / "assets" / "textures" / "espuma_procedural.png"
        )

    def apply(self):
        """Envia o estado da água e depois os ajustes visuais noturnos."""
        super().apply()
        uniform = self.nightUniforms
        NoiteLightingContext._enviar_uniform(uniform["u_exposure"], self.exposure)
        NoiteLightingContext._enviar_uniform(uniform["u_gamma"], self.gamma)
        NoiteLightingContext._enviar_uniform(uniform["u_fog_density"], self.fogDensity)
        _enviar_luzes_pontuais(
            self.pointLightUniforms,
            self.lighting.point_lights_eye,
            self.lighting.point_light_count,
        )

        for index, wave in enumerate(C.WATER_DETAIL_WAVES):
            direction_x, direction_z, amplitude, wave_number, speed = wave
            localizacao = self.waterUniforms[f"u_wave{3 + index}"]
            if localizacao != -1:
                glUniform4f(
                    localizacao,
                    direction_x,
                    direction_z,
                    amplitude,
                    wave_number,
                )
            NoiteLightingContext._enviar_uniform(
                self.waterUniforms[f"u_wave_speed{3 + index}"],
                speed,
            )

        NoiteLightingContext._enviar_uniform(
            self.waterUniforms["u_foam_scale"], C.WATER_FOAM_SCALE
        )
        NoiteLightingContext._enviar_uniform(
            self.waterUniforms["u_foam_strength"], C.WATER_FOAM_STRENGTH
        )
        NoiteLightingContext._enviar_uniform(
            self.waterUniforms["u_specular_strength"], C.WATER_SPECULAR_STRENGTH
        )
        if self.waterUniforms["u_foam_texture"] != -1:
            glUniform1i(self.waterUniforms["u_foam_texture"], 2)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.foamTexture.textureID)
        glActiveTexture(GL_TEXTURE0)
