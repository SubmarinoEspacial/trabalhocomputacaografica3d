"""Shader Lambert local, com materiais que compartilham a luz direcional.

Fonte conceitual: modelo difuso Lambert no capítulo 6, "Lights", de Stemkoski
e Pascale (2022). Este shader é uma implementação original do projeto.
"""
import math

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_VERTEX_SHADER,
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
    glUniform1i,
    glUniform3f,
    glUseProgram,
)


_VERTEX_SHADER = """
#version 120
varying vec3 v_normal_eye;
varying vec2 v_uv;

void main() {
    vec4 posicao_olho = gl_ModelViewMatrix * gl_Vertex;
    v_normal_eye = normalize(gl_NormalMatrix * gl_Normal);
    v_uv = gl_MultiTexCoord0.xy;
    gl_Position = gl_ProjectionMatrix * posicao_olho;
}
"""

_FRAGMENT_SHADER = """
#version 120
uniform vec3 u_light_direction_eye;
uniform vec3 u_light_ambient;
uniform vec3 u_light_diffuse;
uniform vec3 u_material_color;
uniform int u_use_texture;
uniform sampler2D u_texture;
varying vec3 v_normal_eye;
varying vec2 v_uv;

void main() {
    vec3 cor_base = u_material_color;
    if (u_use_texture != 0) {
        cor_base *= texture2D(u_texture, v_uv).rgb;
    }

    // A normal transformada continua perpendicular a superficie apos o modelo/camera.
    vec3 normal = normalize(v_normal_eye);
    vec3 direcao_para_luz = normalize(-u_light_direction_eye);
    // Lambert: o produto normal-luz controla o brilho difuso local de cada fragmento.
    float difuso = max(dot(normal, direcao_para_luz), 0.0);
    vec3 iluminacao = u_light_ambient + u_light_diffuse * difuso;
    gl_FragColor = vec4(cor_base * iluminacao, 1.0);
}
"""


class LightingContext:
    """Compila uma vez o shader e compartilha uniforms entre todos os materiais."""

    _UNIFORMS = (
        "u_light_direction_eye",
        "u_light_ambient",
        "u_light_diffuse",
        "u_material_color",
        "u_use_texture",
        "u_texture",
    )

    def __init__(self, light):
        self.light = light
        self.yaw_camera = 0.0
        self.pitch_camera = 0.0
        self.program = self._build_program()
        self.uniforms = {
            nome: glGetUniformLocation(self.program, nome) for nome in self._UNIFORMS
        }

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
        vertex_shader = self._compilar(GL_VERTEX_SHADER, _VERTEX_SHADER)
        fragment_shader = self._compilar(GL_FRAGMENT_SHADER, _FRAGMENT_SHADER)
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

    def _direcao_no_espaco_visual(self):
        """Transforma a direção mundial pelo giro inverso aplicado à câmera."""
        yaw = math.radians(-self.yaw_camera)
        pitch = math.radians(-self.pitch_camera)
        dx, dy, dz = self.light.direction

        x_yaw = math.cos(yaw) * dx + math.sin(yaw) * dz
        y_yaw = dy
        z_yaw = -math.sin(yaw) * dx + math.cos(yaw) * dz
        x_eye = x_yaw
        y_eye = math.cos(pitch) * y_yaw - math.sin(pitch) * z_yaw
        z_eye = math.sin(pitch) * y_yaw + math.cos(pitch) * z_yaw
        comprimento = math.sqrt(x_eye * x_eye + y_eye * y_eye + z_eye * z_eye)
        return (x_eye / comprimento, y_eye / comprimento, z_eye / comprimento)

    def activate(self):
        """Seleciona o programa e envia os uniforms da fonte de luz única."""
        glUseProgram(self.program)
        direcao = self._direcao_no_espaco_visual()
        glUniform3f(self.uniforms["u_light_direction_eye"], *direcao)
        glUniform3f(self.uniforms["u_light_ambient"], *self.light.ambient)
        glUniform3f(self.uniforms["u_light_diffuse"], *self.light.diffuse)


class LambertMaterial:
    """Material Lambert de cor uniforme ou combinado com uma textura."""

    def __init__(self, lighting, color, texture_id=None):
        self.lighting = lighting
        self.color = tuple(color)
        self.texture_id = texture_id

    def apply(self):
        """Envia cor/textura e uniforms para o shader Lambert compartilhado."""
        self.lighting.activate()
        glUniform3f(self.lighting.uniforms["u_material_color"], *self.color)
        usa_textura = self.texture_id is not None
        glUniform1i(self.lighting.uniforms["u_use_texture"], int(usa_textura))
        glUniform1i(self.lighting.uniforms["u_texture"], 0)
        if usa_textura:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def unapply(self):
        """Limpa a textura e retorna ao pipeline padrão após desenhar a malha."""
        if self.texture_id is not None:
            glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)