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

import math

from core.texture import Texture
from light.shadow_map import _camera_view_matrix
from material.lambert import LambertMaterial, LightingContext
from material.phong import PhongMaterial
from material.water import WaterMaterial
from src import config as C


_UNIFORMS_NOTURNOS = ("u_exposure", "u_gamma", "u_fog_density")
_UNIFORMS_AGUA = (
    "u_wave3", "u_wave_speed3", "u_wave4", "u_wave_speed4",
    "u_foam_texture", "u_foam_scale", "u_foam_strength", "u_specular_strength",
    "u_pcf_samples", "u_wave_count",
)
_MAX_SLOTS_LUZ = 4
_LUZ_APAGADA = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0)


def _localizacoes_luzes_pontuais(program):
    """Consulta os uniforms dos quatro slots de luzes pontuais."""
    return {
        "count": glGetUniformLocation(program, "u_point_light_count"),
        "position": tuple(
            glGetUniformLocation(program, f"u_point_light_position_eye[{i}]")
            for i in range(_MAX_SLOTS_LUZ)
        ),
        "color": tuple(
            glGetUniformLocation(program, f"u_point_light_color[{i}]")
            for i in range(_MAX_SLOTS_LUZ)
        ),
        "range": tuple(
            glGetUniformLocation(program, f"u_point_light_range[{i}]")
            for i in range(_MAX_SLOTS_LUZ)
        ),
    }


def _enviar_luzes_pontuais(uniforms, luzes_olho, quantidade):
    """Envia apenas as luzes ativas e mantém os slots restantes apagados."""
    quantidade = max(0, min(int(quantidade), C.MAX_POINT_LIGHTS, _MAX_SLOTS_LUZ))
    if uniforms["count"] != -1:
        glUniform1i(uniforms["count"], quantidade)
    for index in range(_MAX_SLOTS_LUZ):
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
        self.pcfSamplesLocation = glGetUniformLocation(self.program, "u_pcf_samples")
        self.point_light_count = 0
        self._point_lights_eye = tuple(
            _LUZ_APAGADA for _ in range(_MAX_SLOTS_LUZ)
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
        while len(slots) < _MAX_SLOTS_LUZ:
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
        if self.pcfSamplesLocation != -1:
            glUniform1i(self.pcfSamplesLocation, C.SHADOW_PCF_SAMPLES)
        _enviar_luzes_pontuais(
            self.pointLightUniforms,
            self._point_lights_eye,
            self.point_light_count,
        )



def _direcao_fill_no_espaco_visual(lighting):
    """Converte PRESENT_FILL_SOURCE (mundo) para o espaço do olho, como a lua."""
    fonte = C.PRESENT_FILL_SOURCE
    norma = math.sqrt(sum(componente * componente for componente in fonte)) or 1.0
    normalizada = tuple(componente / norma for componente in fonte)
    return lighting._direcao_no_espaco_visual(normalizada)


class _VeiculoPresentMixin:
    """Envia os uniforms do modo apresentação (só usado nos veículos)."""

    def _enviar_apresentacao(self):
        lighting = self.lighting
        # No passe de sombra (depth_pass) não há programa de material ativo.
        if getattr(lighting, "depth_pass", False):
            return
        uni = lighting.uniforms
        glUniform1i(uni["u_present_mode"], int(C.PRESENT_MODE))
        glUniform3f(uni["u_present_ambient_top"], *C.PRESENT_AMBIENT_TOP)
        glUniform3f(uni["u_present_ambient_bottom"], *C.PRESENT_AMBIENT_BOTTOM)
        glUniform1f(uni["u_present_ambient"], C.PRESENT_AMBIENT)
        glUniform3f(uni["u_present_fill_dir"], *_direcao_fill_no_espaco_visual(lighting))
        glUniform3f(uni["u_present_fill_color"], *C.PRESENT_FILL_COLOR)
        glUniform1f(uni["u_present_fill"], C.PRESENT_FILL)
        glUniform3f(uni["u_present_rim_color"], *C.PRESENT_RIM_COLOR)
        glUniform1f(uni["u_present_rim"], C.PRESENT_RIM)
        glUniform1f(uni["u_present_rim_power"], C.PRESENT_RIM_POWER)
        glUniform1f(uni["u_present_fog_factor"], C.PRESENT_FOG_FACTOR)
        glUniform1f(uni["u_vehicle_exposure"], C.PRESENT_VEHICLE_EXPOSURE)


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



class VehiclePhongMaterial(_VeiculoPresentMixin, PhongMaterial):
    """PhongMaterial com modo apresentação: realça a forma dos veículos."""

    def apply(self):
        super().apply()
        self._enviar_apresentacao()


class VehicleTexturedPhongMaterial(_VeiculoPresentMixin, TexturedPhongMaterial):
    """TexturedPhongMaterial com o mesmo modo apresentação dos veículos."""

    def apply(self):
        super().apply()
        self._enviar_apresentacao()

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
        if self.waterUniforms["u_pcf_samples"] != -1:
            glUniform1i(self.waterUniforms["u_pcf_samples"], C.SHADOW_PCF_SAMPLES)
        if self.waterUniforms["u_wave_count"] != -1:
            glUniform1i(self.waterUniforms["u_wave_count"], C.WATER_WAVE_COUNT)

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
