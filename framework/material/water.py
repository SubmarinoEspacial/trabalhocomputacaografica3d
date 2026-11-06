"""Material da superfície com ondas analíticas, Fresnel, fog e shadow map."""
from pathlib import Path

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
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
    glUniform4f,
    glUniformMatrix4fv,
    glUseProgram,
)
from src import config as C


class WaterMaterial:
    """Material transparente; recebe sombra, mas a superfície não a projeta."""

    transparent = True
    casts_shadow = False

    def __init__(self, lighting):
        self.lighting = lighting
        self.time = 0.0
        self.program = self._build_program()
        nomes = (
            "u_time", "u_water_level", "u_wave0", "u_wave_speed0",
            "u_wave1", "u_wave_speed1", "u_wave2", "u_wave_speed2",
            "u_light_direction_eye", "u_light_ambient", "u_light_diffuse",
            "u_shadow_map", "u_shadow_texel_size", "u_shadow_bias",
            "u_shadow_enabled", "u_receive_shadow", "u_light_view_projection_eye",
            "u_water_color", "u_sky_color", "u_water_alpha", "u_fog_start", "u_fog_end",
        )
        self.uniforms = {name: glGetUniformLocation(self.program, name) for name in nomes}

    @staticmethod
    def _compile(shader_type, source):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            log = glGetShaderInfoLog(shader)
            raise RuntimeError(log.decode("utf-8", errors="replace") if isinstance(log, bytes) else str(log))
        return shader

    def _build_program(self):
        shader_dir = Path(__file__).resolve().parents[2] / "shaders"
        vertex = self._compile(GL_VERTEX_SHADER, (shader_dir / "water.vert").read_text(encoding="utf-8"))
        fragment = self._compile(GL_FRAGMENT_SHADER, (shader_dir / "water.frag").read_text(encoding="utf-8"))
        program = glCreateProgram()
        glAttachShader(program, vertex)
        glAttachShader(program, fragment)
        glDeleteShader(vertex)
        glDeleteShader(fragment)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            log = glGetProgramInfoLog(program)
            raise RuntimeError(log.decode("utf-8", errors="replace") if isinstance(log, bytes) else str(log))
        return program

    def setTime(self, animationTime):
        """Usa o tempo acumulado da animação, que permanece fixo na pausa."""
        self.time = float(animationTime)

    def apply(self):
        """Envia ondas, luz, neblina e depth map antes do desenho transparente."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform1f(uniform["u_time"], self.time)
        glUniform1f(uniform["u_water_level"], C.WATER_LEVEL)
        for index, wave in enumerate(C.WATER_WAVES):
            direction_x, direction_z, amplitude, wave_number, speed = wave
            glUniform4f(uniform[f"u_wave{index}"], direction_x, direction_z, amplitude, wave_number)
            glUniform1f(uniform[f"u_wave_speed{index}"], speed)

        light = self.lighting.light
        ambient = self.lighting.ambientLight
        direction_eye = self.lighting._direcao_no_espaco_visual()
        glUniform3f(uniform["u_light_direction_eye"], *direction_eye)
        glUniform3f(uniform["u_light_ambient"], *(v * ambient.strength for v in ambient.color))
        glUniform3f(uniform["u_light_diffuse"], *(v * light.strength for v in light.color))
        matrix = self.lighting.shadow_matrix_eye.astype("float32").flatten(order="F")
        glUniformMatrix4fv(uniform["u_light_view_projection_eye"], 1, GL_FALSE, matrix)
        glUniform1i(uniform["u_shadow_map"], 1)
        glUniform2f(
            uniform["u_shadow_texel_size"],
            1.0 / self.lighting.shadow_size[0],
            1.0 / self.lighting.shadow_size[1],
        )
        glUniform1f(uniform["u_shadow_bias"], self.lighting.shadow_bias * 1.5)
        receives_shadow = self.lighting.receiveShadow
        glUniform1i(uniform["u_receive_shadow"], int(receives_shadow))
        glUniform1i(uniform["u_shadow_enabled"], int(receives_shadow and self.lighting.shadow_texture != 0))
        glUniform3f(uniform["u_water_color"], *C.WATER_COLOR)
        glUniform3f(uniform["u_sky_color"], *C.FOG_COLOR)
        glUniform1f(uniform["u_water_alpha"], C.WATER_ALPHA)
        glUniform1f(uniform["u_fog_start"], C.FOG_START)
        glUniform1f(uniform["u_fog_end"], C.FOG_END)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.lighting.shadow_texture)

    def unapply(self):
        """Desativa o shader da água ao terminar o passe transparente."""
        glUseProgram(0)