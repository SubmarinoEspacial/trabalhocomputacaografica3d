"""Shader Lambert local, com materiais que compartilham a luz direcional.

Fonte conceitual: modelo difuso Lambert no capítulo 6, "Lights", de Stemkoski
e Pascale (2022). Este shader é uma implementação original do projeto.
"""
import math
from pathlib import Path

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    GL_VERTEX_SHADER,
    GL_FALSE,
    glActiveTexture,
    glAttachShader,
    glBindTexture,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUniform3f,
    glUniformMatrix3fv,
    glUniformMatrix4fv,
    glUseProgram,
)


class LightingContext:
    """Compila uma vez o shader e compartilha uniforms entre todos os materiais."""

    _UNIFORMS = (
        "u_light_direction_eye",
        "u_light_ambient",
        "u_light_diffuse",
        "u_material_color",
        "u_material_alpha",
        "u_emissive_color",
        "u_emissive_strength",
        "u_material_specular",
        "u_material_shininess",
        "repeatUV",
        "offsetUV",
        "u_use_texture",
        "u_texture",
        "u_light_view_projection_eye",
        "u_shadow_map",
        "u_shadow_texel_size",
        "u_shadow_bias",
        "u_shadow_enabled",
        "u_receive_shadow",
        "u_fog_color",
        "u_fog_start",
        "u_fog_end",
        # Uniforms do modo apresentação dos veículos (padrão seguro: desligado).
        "u_view_transpose",
        "u_present_mode",
        "u_present_ambient_top",
        "u_present_ambient_bottom",
        "u_present_ambient",
        "u_present_fill_dir",
        "u_present_fill_color",
        "u_present_fill",
        "u_present_rim_color",
        "u_present_rim",
        "u_present_rim_power",
        "u_present_fog_factor",
        "u_vehicle_exposure",
    )

    def __init__(self, light, ambientLight=None, fogColor=(0.52, 0.78, 0.92), fogStart=32.0, fogEnd=110.0):
        self.light = light
        self.ambientLight = ambientLight
        self.fogColor = tuple(fogColor)
        self.fogStart = float(fogStart)
        self.fogEnd = float(fogEnd)
        self.yaw_camera = 0.0
        self.pitch_camera = 0.0
        self.shadow_texture = 0
        self.shadow_size = (1, 1)
        self.shadow_bias = 0.001
        self.shadow_matrix_eye = None
        self.depth_pass = False
        self.receiveShadow = False
        self.program = self._build_program()
        self.uniforms = {
            nome: glGetUniformLocation(self.program, nome) for nome in self._UNIFORMS
        }
        # Cache "dirty": luz, câmera, sombra e névoa são iguais para todos os
        # materiais do mesmo quadro. Sem isto, cada Mesh reenviava ~20 uniforms.
        self._uniformes_compartilhados_sujos = True

    @staticmethod
    def _compilar(tipo, fonte):
        shader = glCreateShader(tipo)
        glShaderSource(shader, fonte)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            log = glGetShaderInfoLog(shader)
            if isinstance(log, bytes):
                log = log.decode("utf-8", errors="replace")
            raise RuntimeError(f"Falha ao compilar shader Lambert: {log}")
        return shader

    def _build_program(self):
        shader_dir = Path(__file__).resolve().parents[2] / "shaders"
        vertex_shader = self._compilar(
            GL_VERTEX_SHADER,
            (shader_dir / "material.vert").read_text(encoding="utf-8"),
        )
        fragment_shader = self._compilar(
            GL_FRAGMENT_SHADER,
            (shader_dir / "material.frag").read_text(encoding="utf-8"),
        )
        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        if not glGetProgramiv(program, GL_LINK_STATUS):
            log = glGetProgramInfoLog(program)
            if isinstance(log, bytes):
                log = log.decode("utf-8", errors="replace")
            raise RuntimeError(f"Falha ao vincular shader Lambert: {log}")
        return program

    def set_camera_rotation(self, yaw_degrees, pitch_degrees):
        """Mantém a direção da luz no mesmo espaço visual que as normais."""
        self.yaw_camera = yaw_degrees
        self.pitch_camera = pitch_degrees
        self._uniformes_compartilhados_sujos = True

    def setCameraRotation(self, yawDegrees, pitchDegrees):
        """Alias camelCase para a orientação da câmera usada pela luz."""
        self.set_camera_rotation(yawDegrees, pitchDegrees)

    def set_shadow_map(self, texture_id, size, bias):
        """Vincula o depth texture e o bias que serao comparados no fragmento."""
        self.shadow_texture = texture_id
        self.shadow_size = size
        self.shadow_bias = bias
        self._uniformes_compartilhados_sujos = True

    def setShadowMap(self, textureID, size, bias):
        """Alias camelCase para associar a textura de profundidade."""
        self.set_shadow_map(textureID, size, bias)

    def set_shadow_matrix(self, matrix_eye):
        """Atualiza a matriz que leva coordenadas do olho ao clip da luz."""
        self.shadow_matrix_eye = matrix_eye
        self._uniformes_compartilhados_sujos = True

    def setShadowMatrix(self, matrixEye):
        """Alias camelCase para atualizar a matriz da luz."""
        self.set_shadow_matrix(matrixEye)

    def setReceiveShadow(self, state=True):
        """Define se o material atual recebe comparação com o depth map."""
        self.receiveShadow = bool(state)

    def begin_depth_pass(self, depth_program):
        """Usa temporariamente o shader simples ao desenhar o depth target."""
        self.depth_pass = True
        glUseProgram(depth_program)

    def beginDepthPass(self, depthProgram):
        """Alias camelCase para iniciar o primeiro passe de sombra."""
        self.begin_depth_pass(depthProgram)

    def end_depth_pass(self):
        """Restaura a selecao normal de programas por material."""
        self.depth_pass = False
        glUseProgram(0)

    def endDepthPass(self):
        """Alias camelCase para finalizar o primeiro passe."""
        self.end_depth_pass()

    @staticmethod
    def _matriz_transposta_mundo_olho(yaw_graus, pitch_graus):
        """Devolve Vᵀ (3x3) em coluna-major para devolver normais do olho ao mundo.

        A câmera aplica V = Rx(-pitch)·Ry(-yaw); a transposta troca os sinais,
        então Vᵀ = Ry(yaw)·Rx(pitch). Como (AB)ᵀ = BᵀAᵀ e toda rotação é
        ortogonal, Vᵀ é exatamente a rotação inversa da visão.
        """
        yaw = math.radians(yaw_graus)
        pitch = math.radians(pitch_graus)
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        # Linhas de Vᵀ = Ry(yaw)·Rx(pitch).
        linhas = (
            (cy, sy * sp, sy * cp),
            (0.0, cp, -sp),
            (-sy, cy * sp, cy * cp),
        )
        # glUniformMatrix3fv(GL_FALSE) espera ordem coluna-major.
        return tuple(linhas[j][i] for i in range(3) for j in range(3))

    def _direcao_no_espaco_visual(self, direcao=None):
        """Transforma a direção mundial pelo giro inverso aplicado à câmera."""
        yaw = math.radians(-self.yaw_camera)
        pitch = math.radians(-self.pitch_camera)
        dx, dy, dz = direcao if direcao is not None else self.light.direction

        x_yaw = math.cos(yaw) * dx + math.sin(yaw) * dz
        y_yaw = dy
        z_yaw = -math.sin(yaw) * dx + math.cos(yaw) * dz
        x_eye = x_yaw
        y_eye = math.cos(pitch) * y_yaw - math.sin(pitch) * z_yaw
        z_eye = math.sin(pitch) * y_yaw + math.cos(pitch) * z_yaw
        comprimento = math.sqrt(x_eye * x_eye + y_eye * y_eye + z_eye * z_eye)
        return (x_eye / comprimento, y_eye / comprimento, z_eye / comprimento)

    def _enviar_uniforms_compartilhados(self):
        """Envia luz/câmera/sombra/nevoa uma vez por quadro, não por material."""
        direcao = self._direcao_no_espaco_visual()
        glUniform3f(self.uniforms["u_light_direction_eye"], *direcao)
        ambient_color = self.ambientLight.color if self.ambientLight else (0.16, 0.17, 0.19)
        ambient_strength = self.ambientLight.strength if self.ambientLight else 1.0
        glUniform3f(
            self.uniforms["u_light_ambient"],
            *(componente * ambient_strength for componente in ambient_color),
        )
        glUniform3f(
            self.uniforms["u_light_diffuse"],
            *(componente * self.light.strength for componente in self.light.color),
        )
        if self.shadow_matrix_eye is None:
            matrix = (0.0,) * 16
        else:
            matrix = self.shadow_matrix_eye.astype("float32").flatten(order="F")
        glUniformMatrix4fv(self.uniforms["u_light_view_projection_eye"], 1, GL_FALSE, matrix)
        glUniformMatrix3fv(
            self.uniforms["u_view_transpose"], 1, GL_FALSE,
            self._matriz_transposta_mundo_olho(self.yaw_camera, self.pitch_camera),
        )
        glUniform3f(self.uniforms["u_fog_color"], *self.fogColor)
        glUniform1f(self.uniforms["u_fog_start"], self.fogStart)
        glUniform1f(self.uniforms["u_fog_end"], self.fogEnd)
        glUniform1i(self.uniforms["u_shadow_map"], 1)
        glUniform2f(
            self.uniforms["u_shadow_texel_size"],
            1.0 / self.shadow_size[0],
            1.0 / self.shadow_size[1],
        )
        glUniform1f(self.uniforms["u_shadow_bias"], self.shadow_bias)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_texture)

    def activate(self):
        """Seleciona o programa e envia os uniforms da fonte de luz única."""
        glUseProgram(self.program)
        if self._uniformes_compartilhados_sujos:
            self._uniformes_compartilhados_sujos = False
            self._enviar_uniforms_compartilhados()
        glUniform1i(
            self.uniforms["u_shadow_enabled"],
            int(self.shadow_texture != 0 and self.receiveShadow),
        )
        glUniform1i(self.uniforms["u_receive_shadow"], int(self.receiveShadow))


class LambertMaterial:
    """Material Lambert de cor uniforme ou combinado com uma textura."""

    def __init__(
        self,
        lighting,
        color,
        texture_id=None,
        alpha=1.0,
        emissive=(0.0, 0.0, 0.0),
        emissiveStrength=1.0,
        repeatUV=(1.0, 1.0),
        offsetUV=(0.0, 0.0),
        specular=(0.0, 0.0, 0.0),
        shininess=1.0,
        transparent=False,
        casts_shadow=True,
    ):
        self.lighting = lighting
        self.color = tuple(color)
        self.texture_id = texture_id
        self.alpha = alpha
        self.emissive = tuple(emissive)
        self.emissiveStrength = float(emissiveStrength)
        self.repeatUV = tuple(repeatUV)
        self.offsetUV = tuple(offsetUV)
        self.specular = tuple(specular)
        self.shininess = float(shininess)
        self.transparent = transparent
        self.casts_shadow = casts_shadow

    def apply(self):
        """Envia cor/textura e uniforms para o shader Lambert compartilhado."""
        if self.lighting.depth_pass:
            return
        self.lighting.activate()
        glUniform3f(self.lighting.uniforms["u_material_color"], *self.color)
        glUniform1f(self.lighting.uniforms["u_material_alpha"], self.alpha)
        glUniform3f(self.lighting.uniforms["u_emissive_color"], *self.emissive)
        glUniform1f(
            self.lighting.uniforms["u_emissive_strength"],
            self.emissiveStrength,
        )
        glUniform2f(self.lighting.uniforms["repeatUV"], *self.repeatUV)
        glUniform2f(self.lighting.uniforms["offsetUV"], *self.offsetUV)
        glUniform3f(self.lighting.uniforms["u_material_specular"], *self.specular)
        glUniform1f(self.lighting.uniforms["u_material_shininess"], self.shininess)
        # O modo apresentação é o único uniform por material; os demais
        # parâmetros são globais do quadro e ficam no contexto noturno.
        glUniform1i(self.lighting.uniforms["u_present_mode"], 0)
        usa_textura = self.texture_id is not None
        glUniform1i(self.lighting.uniforms["u_use_texture"], int(usa_textura))
        glUniform1i(self.lighting.uniforms["u_texture"], 0)
        if usa_textura:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def unapply(self):
        """Limpa a textura e retorna ao pipeline padrão após desenhar a malha."""
        if self.lighting.depth_pass:
            return
        if self.texture_id is not None:
            glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)