"""Qualidade adaptativa com histerese, sem recriar malhas em tempo de execução.

A escada segue a ordem pedida: escala de render → PCF → ondas da água →
luzes pontuais → bloom. Apenas uniforms, alvo de pós-processamento e
parâmetros lidos por frame mudam; nenhuma geometria é reconstruída.
"""
from src import config as C


class QualidadeAdaptativa:
    """Reduz/sobe um degrau conforme a média de FPS, com histerese de tempo."""

    def __init__(self, postprocess):
        self.postprocess = postprocess
        self.ativo = bool(C.ADAPTIVE_QUALITY)
        self.nivel = 0
        self._tempo_baixo = 0.0
        self._tempo_alto = 0.0
        self.recarregar_base()

    def recarregar_base(self):
        """Guarda os valores do perfil atual e recalcula a escada de cortes."""
        self.base = {
            "render_scale": float(C.RENDER_SCALE),
            "pcf": int(C.SHADOW_PCF_SAMPLES),
            "waves": int(C.WATER_WAVE_COUNT),
            "lights": int(C.MAX_POINT_LIGHTS),
            "bloom": bool(C.POST_BLOOM_ENABLED),
        }
        self.escada = self._montar_escada()
        self.nivel = 0
        self._tempo_baixo = 0.0
        self._tempo_alto = 0.0
        self._aplicar_nivel()

    def _montar_escada(self):
        """Cria degraus absolutos a partir do perfil, sem repetir valores."""
        passos = []
        escala = self.base["render_scale"]
        for valor in (0.85, 0.70, 0.50):
            if escala > valor + 1e-6:
                passos.append(("render_scale", valor))
        if self.base["pcf"] > 1:
            passos.append(("pcf", 1))
        if self.base["waves"] > 3:
            passos.append(("waves", 3))
        if self.base["waves"] > 2:
            passos.append(("waves", 2))
        if self.base["lights"] > 1:
            passos.append(("lights", 1))
        if self.base["bloom"]:
            passos.append(("bloom", False))
        return passos

    def _aplicar_nivel(self):
        """Aplica todos os degraus até o nível atual sobre o perfil base."""
        valores = dict(self.base)
        for tipo, valor in self.escada[:self.nivel]:
            chave = {
                "render_scale": "render_scale",
                "pcf": "pcf",
                "waves": "waves",
                "lights": "lights",
                "bloom": "bloom",
            }[tipo]
            valores[chave] = valor

        C.RENDER_SCALE = valores["render_scale"]
        C.SHADOW_PCF_SAMPLES = valores["pcf"]
        C.WATER_WAVE_COUNT = valores["waves"]
        C.MAX_POINT_LIGHTS = valores["lights"]
        C.POST_BLOOM_ENABLED = valores["bloom"]
        if self.postprocess is not None:
            self.postprocess.set_render_scale(C.RENDER_SCALE)

    def alternar(self):
        """Liga/desliga o modo adaptativo (tecla G)."""
        self.ativo = not self.ativo
        self._tempo_baixo = 0.0
        self._tempo_alto = 0.0
        if self.ativo:
            self.recarregar_base()
        return self.ativo

    def update(self, deltaTime, fps):
        """Acumula tempo abaixo/acima do alvo e troca um degrau por vez."""
        if not self.ativo or fps <= 0.0:
            return False
        alvo = max(1.0, float(C.TARGET_FPS))
        abaixo = fps < alvo * C.ADAPTIVE_DOWN_FPS
        acima = fps > alvo * C.ADAPTIVE_UP_FPS
        if abaixo:
            self._tempo_baixo += deltaTime
            self._tempo_alto = 0.0
        elif acima:
            self._tempo_alto += deltaTime
            self._tempo_baixo = 0.0
        else:
            self._tempo_baixo = max(0.0, self._tempo_baixo - deltaTime)
            self._tempo_alto = max(0.0, self._tempo_alto - deltaTime)

        mudou = False
        if (
            self._tempo_baixo >= C.ADAPTIVE_DOWN_TIME
            and self.nivel < len(self.escada)
        ):
            self.nivel += 1
            self._tempo_baixo = 0.0
            mudou = True
        elif self._tempo_alto >= C.ADAPTIVE_UP_TIME and self.nivel > 0:
            self.nivel -= 1
            self._tempo_alto = 0.0
            mudou = True
        if mudou:
            self._aplicar_nivel()
        return mudou

    def descricao(self):
        """Texto curto mostrado no HUD junto do perfil de qualidade."""
        return (
            f"{C.QUALITY}, escala {C.RENDER_SCALE:.2f}, "
            f"nível {self.nivel}/{len(self.escada)}"
        )
