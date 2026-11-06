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
    glUniform1i,
    glUniform1f,
    glUniform3f,
    glUniform2f,
    glUniformMatrix4fv,
    glUseProgram,
)


_VERTEX_SHADER = """
#version 120
// gl_Vertex: posicao local emitida por glVertex; gl_Normal: normal da face.
// gl_MultiTexCoord0: UV do piso; gl_ModelViewMatrix/ProjectionMatrix sao uniforms built-in.
// u_light_view_projection_eye: transforma posicao em espaco de olho para clip da luz.
varying vec3 v_normal_eye;
varying vec2 v_uv;
uniform mat4 u_light_view_projection_eye;
varying vec4 v_shadow_position;

void main() {
    vec4 posicao_olho = gl_ModelViewMatrix * gl_Vertex;
    // gl_NormalMatrix transforma a normal para o mesmo espaco visual da luz.
    v_normal_eye = normalize(gl_NormalMatrix * gl_Normal);
    v_uv = gl_MultiTexCoord0.xy;
    v_shadow_position = u_light_view_projection_eye * posicao_olho;
    gl_Position = gl_ProjectionMatrix * posicao_olho;
}
"""

_FRAGMENT_SHADER = """
#version 120
// Direcao dos raios, ambiente e difuso da luz direcional em espaco de olho.
uniform vec3 u_light_direction_eye;
uniform vec3 u_light_ambient;
uniform vec3 u_light_diffuse;
// Cor do material e selecao/amostragem da textura-base.
uniform vec3 u_material_color;
uniform int u_use_texture;
uniform sampler2D u_texture;
// Mapa de profundidade, tamanho de texel, bias normalizado e liga/desliga.
uniform sampler2D u_shadow_map;
uniform vec2 u_shadow_texel_size;
uniform float u_shadow_bias;
uniform int u_shadow_enabled;
varying vec3 v_normal_eye;
varying vec2 v_uv;
varying vec4 v_shadow_position;

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

    float sombra = 0.0;
    vec3 coordenada_luz = v_shadow_position.xyz / v_shadow_position.w;
    coordenada_luz = coordenada_luz * 0.5 + 0.5;
    if (u_shadow_enabled != 0 &&
        coordenada_luz.x >= 0.0 && coordenada_luz.x <= 1.0 &&
        coordenada_luz.y >= 0.0 && coordenada_luz.y <= 1.0 &&
        coordenada_luz.z >= 0.0 && coordenada_luz.z <= 1.0) {
        // Bias aumenta em faces rasantes; a media 3x3 reduz bordas serrilhadas.
        float bias = max(u_shadow_bias * (1.0 - difuso), u_shadow_bias * 0.2);
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                vec2 deslocamento = vec2(float(x), float(y)) * u_shadow_texel_size;
                float profundidade_luz = texture2D(u_shadow_map, coordenada_luz.xy + deslocamento).r;
                sombra += coordenada_luz.z - bias > profundidade_luz ? 1.0 : 0.0;
            }
        }
        sombra /= 9.0;
    }

    // Este teste escurece a iluminacao local; a profundidade comparada e a sombra projetada.
    vec3 iluminacao = u_light_ambient + u_light_diffuse * difuso * (1.0 - 0.72 * sombra);
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
        "u_light_view_projection_eye",
        "u_shadow_map",
        "u_shadow_texel_size",
        "u_shadow_bias",
        "u_shadow_enabled",
    )

    def __init__(self, light):
        self.light = light
        self.yaw_camera = 0.0
        self.pitch_camera = 0.0
        self.shadow_texture = 0
        self.shadow_size = (1, 1)
        self.shadow_bias = 0.001
        self.shadow_matrix_eye = None
        self.depth_pass = False
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

    def set_shadow_map(self, texture_id, size, bias):
        """Vincula o depth texture e o bias que serao comparados no fragmento."""
        self.shadow_texture = texture_id
        self.shadow_size = size
        self.shadow_bias = bias

    def set_shadow_matrix(self, matrix_eye):
        """Atualiza a matriz que leva coordenadas do olho ao clip da luz."""
        self.shadow_matrix_eye = matrix_eye

    def begin_depth_pass(self, depth_program):
        """Usa temporariamente o shader simples ao desenhar o depth target."""
        self.depth_pass = True
        glUseProgram(depth_program)

    def end_depth_pass(self):
        """Restaura a selecao normal de programas por material."""
        self.depth_pass = False
        glUseProgram(0)

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
        if self.shadow_matrix_eye is None:
            matrix = (0.0,) * 16
        else:
            matrix = self.shadow_matrix_eye.astype("float32").flatten(order="F")
        glUniformMatrix4fv(self.uniforms["u_light_view_projection_eye"], 1, GL_FALSE, matrix)
        glUniform1i(self.uniforms["u_shadow_enabled"], int(self.shadow_texture != 0))
        glUniform1i(self.uniforms["u_shadow_map"], 1)
        glUniform2f(
            self.uniforms["u_shadow_texel_size"],
            1.0 / self.shadow_size[0],
            1.0 / self.shadow_size[1],
        )
        glUniform1f(self.uniforms["u_shadow_bias"], self.shadow_bias)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_texture)


class LambertMaterial:
    """Material Lambert de cor uniforme ou combinado com uma textura."""

    def __init__(self, lighting, color, texture_id=None):
        self.lighting = lighting
        self.color = tuple(color)
        self.texture_id = texture_id

    def apply(self):
        """Envia cor/textura e uniforms para o shader Lambert compartilhado."""
        if self.lighting.depth_pass:
            return
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
        if self.lighting.depth_pass:
            return
        if self.texture_id is not None:
            glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)