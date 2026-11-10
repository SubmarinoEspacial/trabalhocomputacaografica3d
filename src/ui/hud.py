"""HUD sobreposto compacto: FPS, dica/lista de controles e painel Sobre.

O HUD desenha depois de tudo, no framebuffer padrão da janela, com uma
projeção ortográfica própria e quads texturizados — fora da cena OpenGL:
não entra no shadow map, não recebe luz/neblina/exposição e não sofre
tone mapping. Textos viram texturas uma única vez; só o bloco de FPS/estado
é recriado a cada 0,5 s. O caminho de pixels segue o mesmo padrão de
`framework/core/texture.py` (pygame.image.tostring + glTexImage2D), mas com
RGBA, CLAMP_TO_EDGE e blend de alfa.
"""
import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor4f,
    glDeleteTextures,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glPixelStorei,
    glPopMatrix,
    glPushMatrix,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2f,
)

from src import config as C

# Painéis discretos: alpha baixo e sem bordas grossas.
_COR_FUNDO = (0.03, 0.04, 0.07, 0.40)
_COR_FUNDO_BOTOES = (0.16, 0.20, 0.28, 0.55)
_COR_FUNDO_HOVER = (0.32, 0.40, 0.56, 0.72)
_COR_FUNDO_FECHAR = (0.22, 0.12, 0.12, 0.62)
_COR_VEU = (0.0, 0.0, 0.0, 0.35)
# Cores de texto no espaço 0-255 (pygame.font.render); quads usam floats 0-1.
_COR_TEXTO = (224, 232, 245)
_COR_TECLA = (255, 219, 89)
_COR_TITULO = (245, 247, 255)
_COR_SUAVE = (158, 168, 189)    # linhas secundárias (cinza azulado)
_COR_ESTADO = (191, 242, 255)   # nome do estado em azul-gelo
_COR_FPS_OK = (115, 242, 115)
_COR_FPS_MEDIO = (250, 217, 76)
_COR_FPS_RUIM = (250, 89, 76)


def _texto_para_textura(surface):
    """Envia uma Surface RGBA para a GPU seguindo o caminho do framework."""
    largura, altura = surface.get_size()
    pixels = pygame.image.tostring(surface, "RGBA", True)
    textura = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textura)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, largura, altura, 0,
        GL_RGBA, GL_UNSIGNED_BYTE, pixels,
    )
    glBindTexture(GL_TEXTURE_2D, 0)
    return textura, (largura, altura)


def _liberar_textura(textura):
    if textura is not None:
        glDeleteTextures(1, [textura])


class Hud:
    """Gerencia texturas, layout compacto e interação dos elementos da interface."""

    def __init__(self, largura, altura):
        pygame.mouse.set_visible(True)
        self.largura = int(largura)
        self.altura = int(altura)
        # Estados de exibição alternados por teclas/mouse.
        self.hud_oculto = False
        self.mostrar_controles = False   # começa fechado; H abre a lista
        self.mostrar_sobre = False
        # Limitador de FPS: ligado por padrão (clock.tick); V alterna.
        self.limitador_ativo = True
        self.limite_fps = C.FRAME_LIMIT
        self.alvo_fps = C.TARGET_FPS
        # Estado interno da média móvel de 0,5 s.
        self._relogio_acc = 0.0
        self._quadros_acc = 0
        self._proximo_refresh = 0.0
        self._fps = 0.0
        self._frame_ms = 0.0
        self._timings_ema = {}
        self._status = {
            "qualidade": C.QUALITY,
            "escala": C.RENDER_SCALE,
            "adaptativo": C.ADAPTIVE_QUALITY,
            "diagnostico": {},
        }
        # Texturas (criadas sob demanda; _fps_tex só no refresh de 0,5 s).
        self._fps_tex = None
        self._fps_tex_tamanho = (0, 0)
        self._controles_tex = None
        self._controles_tex_tamanho = (0, 0)
        self._dica_tex = None
        self._dica_tex_tamanho = (0, 0)
        self._sobre_tex = None
        self._sobre_tex_tamanho = (0, 0)
        self._sobre_botao_tex = None
        self._sobre_botao_tex_tamanho = (0, 0)
        self._fechar_tex = None
        self._fechar_tex_tamanho = (0, 0)
        self._sobre_hover = False
        self._mouse_anterior = False
        self._construir_fontes()
        self._construir_texturas_estaticas()

    # ---------- construção e redimensionamento ----------
    def _px(self, proporcao):
        """Converte fração da altura da janela em pixels (padding proporcional)."""
        return max(1, int(round(self.altura * proporcao)))

    def _construir_fontes(self):
        """Escolhe uma fonte pequena: ~1,4% a 1,6% da altura, entre 11 e 18 px."""
        altura_texto = max(11, min(18, int(round(self.altura * 0.015 * C.HUD_SCALE))))
        # O tamanho do pygame é em pontos; ~1,5x entrega a altura de glifo desejada.
        fonte_px = max(10, min(28, int(round(altura_texto * 1.5))))
        self.fonte_px = fonte_px
        self.f_texto = pygame.font.Font(None, fonte_px)
        self.f_negrito = pygame.font.Font(None, fonte_px)
        self.f_negrito.set_bold(True)
        self.f_titulo = pygame.font.Font(None, min(28, fonte_px + 2))
        self.f_titulo.set_bold(True)

    def _liberar_estaticas(self):
        for nome in (
            "_controles_tex", "_dica_tex", "_sobre_tex",
            "_sobre_botao_tex", "_fechar_tex",
        ):
            _liberar_textura(getattr(self, nome))
            setattr(self, nome, None)

    def on_resize(self, largura, altura):
        """Refaz fontes e texturas estáticas no novo tamanho da janela."""
        self.largura = int(largura)
        self.altura = int(altura)
        if self.largura <= 0 or self.altura <= 0:
            return
        self._construir_fontes()
        self._liberar_estaticas()
        _liberar_textura(self._fps_tex)
        self._fps_tex = None
        self._construir_texturas_estaticas()

    def _construir_texturas_estaticas(self):
        self._controles_tex, self._controles_tex_tamanho = self._render_lista_controles()
        self._dica_tex, self._dica_tex_tamanho = self._render_simples(
            "H controles | I sobre | F1 ocultar", self.f_texto, _COR_SUAVE,
        )
        self._sobre_tex, self._sobre_tex_tamanho = self._render_sobre()
        self._sobre_botao_tex, self._sobre_botao_tex_tamanho = self._render_simples(
            "? Sobre", self.f_texto, _COR_TEXTO[:3],
        )
        self._fechar_tex, self._fechar_tex_tamanho = self._render_simples(
            "Fechar", self.f_negrito, _COR_TEXTO[:3],
        )

    @staticmethod
    def _render_simples(texto, font, cor_rgb):
        return _texto_para_textura(font.render(texto, True, cor_rgb))

    def _render_lista_controles(self):
        """Renderiza CONTROLS em duas colunas dentro de ~22% x ~18% da janela."""
        largura_max = int(self.largura * 0.22)
        altura_max = int(self.altura * 0.18)
        pad = self._px(0.004)
        gap = self._px(0.006)
        coluna = max(40, (largura_max - 2 * pad - gap) // 2)
        linha_h = self.f_texto.get_height()
        # Duas colunas: metade das entradas em cada uma.
        metade = (len(C.CONTROLS) + 1) // 2
        colunas = (C.CONTROLS[:metade], C.CONTROLS[metade:])
        linhas = max(len(coluna_itens) for coluna_itens in colunas)
        # Distribui as linhas dentro do orçamento vertical (sem cortar entradas).
        passo = min(linha_h, max(1, (altura_max - 2 * pad) // max(1, linhas)))

        superficie = pygame.Surface((largura_max, altura_max), pygame.SRCALPHA)
        superficie.fill((0, 0, 0, 0))
        usado_x = pad
        usado_y = pad
        for indice_coluna, itens in enumerate(colunas):
            x = pad + indice_coluna * (coluna + gap)
            y = pad
            for tecla, descricao in itens:
                tecla_s = self.f_negrito.render(tecla, True, _COR_TECLA[:3])
                desc_s = self.f_texto.render("  " + descricao, True, _COR_TEXTO[:3])
                if tecla_s.get_width() + desc_s.get_width() > coluna:
                    # Trunca a descrição com reticências para caber na coluna.
                    texto = descricao
                    while texto and self.f_texto.size("  " + texto + "…")[0] > (
                        coluna - tecla_s.get_width()
                    ):
                        texto = texto[:-1]
                    desc_s = self.f_texto.render(
                        "  " + texto + "…", True, _COR_TEXTO[:3],
                    )
                superficie.blit(tecla_s, (x, y))
                superficie.blit(desc_s, (x + tecla_s.get_width(), y))
                usado_x = max(usado_x, x + tecla_s.get_width() + desc_s.get_width())
                usado_y = max(usado_y, y + linha_h)
                y += passo
        # Corta a textura no conteúdo real: o painel não fica com área vazia.
        largura_usada = min(largura_max, usado_x + pad)
        altura_usada = min(altura_max, usado_y + pad)
        superficie = superficie.subsurface(
            (0, 0, max(1, largura_usada), max(1, altura_usada)),
        ).copy()
        return _texto_para_textura(superficie)

    @staticmethod
    def _quebrar_texto(texto, font, largura_max):
        """Quebra o texto em linhas que cabem na largura do painel."""
        linhas_finais = []
        for paragrafo in texto.split("\n"):
            if not paragrafo.strip():
                linhas_finais.append("")
                continue
            palavras = paragrafo.split()
            atual = ""
            for palavra in palavras:
                tentativa = (atual + " " + palavra).strip()
                if font.size(tentativa)[0] <= largura_max:
                    atual = tentativa
                else:
                    if atual:
                        linhas_finais.append(atual)
                    atual = palavra
            linhas_finais.append(atual)
        return linhas_finais

    def _render_sobre(self):
        """Renderiza título + resumo do painel Sobre (até ~8 linhas, bem menor)."""
        pad = self._px(0.010)
        # O retângulo final acrescenta mais 2*pad; reserva ambos para caber
        # de fato nos limites de ~45% x ~50% da janela.
        largura_max = max(120, int(self.largura * 0.45) - 4 * pad)
        altura_max = max(40, int(self.altura * 0.50) - 4 * pad)
        linhas = []
        titulo_linhas = self._quebrar_texto(C.ABOUT_TITLE, self.f_titulo, largura_max)
        for linha in titulo_linhas:
            linhas.append((self.f_titulo, linha, _COR_TITULO[:3]))
        linhas.append((self.f_texto, "", _COR_TEXTO[:3]))
        for linha in self._quebrar_texto(C.ABOUT_TEXT, self.f_texto, largura_max):
            linhas.append((self.f_texto, linha, _COR_TEXTO[:3]))
        creditos = "Créditos: " + " · ".join(C.STUDENT_NAMES)
        for linha in self._quebrar_texto(creditos, self.f_texto, largura_max):
            linhas.append((self.f_texto, linha, _COR_SUAVE))
        for linha in self._quebrar_texto(
            "Referência: Stemkoski e Pascale (2022)", self.f_texto, largura_max,
        ):
            linhas.append((self.f_texto, linha, _COR_SUAVE))

        linha_h = self.f_texto.get_height()
        altura_texto = len(linhas) * linha_h + 2 * pad
        if altura_texto > altura_max:
            # Mantém o limite de ~50% da altura: corta as últimas linhas.
            limite = max(1, (altura_max - 2 * pad) // linha_h)
            linhas = linhas[:limite]
            altura_texto = len(linhas) * linha_h + 2 * pad

        largura_total = min(
            largura_max + 2 * pad,
            max(
                (fonte.size(texto)[0] for fonte, texto, _ in linhas if texto),
                default=1,
            ) + 2 * pad,
        )
        superficie = pygame.Surface((largura_total, altura_texto), pygame.SRCALPHA)
        superficie.fill((0, 0, 0, 0))
        y = pad
        for fonte, texto, cor in linhas:
            if texto:
                superficie.blit(fonte.render(texto, True, cor), (pad, y))
            y += linha_h
        return _texto_para_textura(superficie)

    # ---------- atualização por quadro ----------
    def atualizar(
        self,
        deltaTime,
        estado_nome,
        timings=None,
        perfil_ativo=False,
        diagnostico=None,
        alvo_fps=None,
        qualidade=None,
        escala=None,
        adaptativo=None,
    ):
        """Atualiza a média móvel de FPS; reconstrói a textura a cada 0,5 s."""
        self._relogio_acc += deltaTime
        self._quadros_acc += 1
        self._proximo_refresh += deltaTime
        if alvo_fps is not None:
            self.alvo_fps = int(alvo_fps)
        if qualidade is not None:
            self._status["qualidade"] = qualidade
        if escala is not None:
            self._status["escala"] = float(escala)
        if adaptativo is not None:
            self._status["adaptativo"] = bool(adaptativo)
        if diagnostico is not None:
            self._status["diagnostico"] = dict(diagnostico)
        if timings:
            # Média exponencial simples (alpha = 0.15) das medidas por etapa.
            for chave, valor in timings.items():
                anterior = self._timings_ema.get(chave)
                if anterior is None:
                    self._timings_ema[chave] = valor
                else:
                    self._timings_ema[chave] = 0.85 * anterior + 0.15 * valor
        if self._proximo_refresh >= 0.5:
            elapsed = self._relogio_acc
            self._fps = self._quadros_acc / max(elapsed, 1e-6)
            self._frame_ms = 1000.0 * elapsed / max(1, self._quadros_acc)
            self._relogio_acc = 0.0
            self._quadros_acc = 0
            self._proximo_refresh = 0.0
            self._reconstruir_fps_tex(estado_nome, perfil_ativo)

    def fps(self):
        """Média recente de FPS usada pela qualidade adaptativa."""
        return self._fps

    def alternar_limite(self):
        self.limitador_ativo = not self.limitador_ativo
        return self.limitador_ativo

    def alternar_controles(self):
        self.mostrar_controles = not self.mostrar_controles

    def alternar_sobre(self):
        self.mostrar_sobre = not self.mostrar_sobre

    def fechar_sobre(self):
        self.mostrar_sobre = False

    def alternar_hud(self):
        self.hud_oculto = not self.hud_oculto
        return self.hud_oculto

    def sobre_aberto(self):
        return self.mostrar_sobre

    def _cor_fps(self):
        if self._fps >= 55.0:
            return _COR_FPS_OK
        if self._fps >= 30.0:
            return _COR_FPS_MEDIO
        return _COR_FPS_RUIM

    def _reconstruir_fps_tex(self, estado_nome, perfil_ativo):
        """Monta a linha compacta de FPS e, com F3, o diagnóstico resumido."""
        pad = self._px(0.003)
        linhas = []
        # Primeira linha: métricas principais em uma única faixa.
        linhas.append((
            f"{self._fps:.0f} FPS | {self._frame_ms:.1f} ms | {estado_nome}"
            f" | Alvo: {self.alvo_fps}",
            self.f_negrito,
            self._cor_fps(),
        ))
        rotulos = {"baixa": "baixa", "media": "média", "alta": "alta"}
        qualidade = rotulos.get(str(self._status["qualidade"]), self._status["qualidade"])
        escala = self._status["escala"]
        adaptativo = "on" if self._status["adaptativo"] else "off"
        linhas.append((
            f"Qualidade: {qualidade}, escala {escala:.2f} | Adaptativo: {adaptativo}",
            self.f_texto,
            _COR_SUAVE,
        ))

        diagnostico = self._status["diagnostico"]
        if perfil_ativo and diagnostico:
            linhas.append((
                f"GL: {diagnostico.get('renderer', '?')} | {diagnostico.get('version', '?')}",
                self.f_texto,
                _COR_SUAVE,
            ))
            linhas.append((
                f"Janela: {diagnostico.get('janela', '?')} | "
                f"Sombra: {diagnostico.get('sombra_res', '?')}px "
                f"PCF {diagnostico.get('pcf', '?')} | "
                f"Luzes: {diagnostico.get('luzes', '?')}",
                self.f_texto,
                _COR_SUAVE,
            ))
            linhas.append((
                f"Draws: principal {diagnostico.get('draws_principal', '?')} | "
                f"sombra {diagnostico.get('draws_sombra', '?')} | "
                f"Meshes: {diagnostico.get('meshes', '?')}"
                f"/{diagnostico.get('meshes_sombra', '?')} | "
                f"Água: {diagnostico.get('agua_vtx', '?')} vtx",
                self.f_texto,
                _COR_SUAVE,
            ))
            partes = []
            for chave in ("logica", "arvore", "sombra", "principal", "pos", "hud"):
                valor = self._timings_ema.get(chave)
                if valor is not None:
                    partes.append(f"{chave} {valor * 1000:.2f}")
            if partes:
                linhas.append((" | ".join(partes) + " ms", self.f_texto, _COR_SUAVE))

        superficies = []
        largura_max = 0
        for texto, fonte, cor in linhas:
            superficie = fonte.render(texto, True, cor)
            superficies.append(superficie)
            largura_max = max(largura_max, superficie.get_width())
        linha_h = self.f_texto.get_height()
        altura_total = len(superficies) * linha_h + 2 * pad
        superficie_total = pygame.Surface((largura_max + 2 * pad, altura_total), pygame.SRCALPHA)
        y = pad
        for superficie in superficies:
            superficie_total.blit(superficie, (pad, y))
            y += linha_h
        _liberar_textura(self._fps_tex)
        self._fps_tex, self._fps_tex_tamanho = _texto_para_textura(superficie_total)

    # ---------- interação de mouse ----------
    def _margem(self):
        return self._px(0.012)

    def _sobre_botao_rect(self):
        largura, altura = self._sobre_botao_tex_tamanho
        pad = self._px(0.005)
        margem = self._margem()
        return (
            self.largura - margem - (largura + 2 * pad),
            margem,
            largura + 2 * pad,
            altura + 2 * pad,
        )

    def _sobre_painel_rect(self):
        largura, altura = self._sobre_tex_tamanho
        pad = self._px(0.010)
        pw, ph = largura + 2 * pad, altura + 2 * pad
        return ((self.largura - pw) // 2, (self.altura - ph) // 2, pw, ph)

    def _fechar_rect(self):
        px, py, pw, ph = self._sobre_painel_rect()
        pad = self._px(0.004)
        tw, th = self._fechar_tex_tamanho
        bw, bh = tw + 2 * pad, th + 2 * pad
        return (px + pw - bw - pad, py + pad, bw, bh)

    @staticmethod
    def _dentro(rect, pos):
        x, y, w, h = rect
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h

    def tratar_mouse(self, posicao, pressionado):
        """Clique no botão Sobre e hover; hit-test em pixels da janela."""
        botao = self._sobre_botao_rect()
        hover = self._dentro(botao, posicao)
        if hover != self._sobre_hover:
            self._sobre_hover = hover
            try:
                pygame.mouse.set_cursor(
                    pygame.SYSTEM_CURSOR_HAND if hover else pygame.SYSTEM_CURSOR_ARROW
                )
            except Exception:
                pass  # alguns drivers não expõem o cursor de mão
        clicou = pressionado and not self._mouse_anterior
        if clicou:
            if self._dentro(botao, posicao):
                self.alternar_sobre()
            elif self.mostrar_sobre:
                painel = self._sobre_painel_rect()
                if self._dentro(self._fechar_rect(), posicao) or not self._dentro(painel, posicao):
                    self.fechar_sobre()
        self._mouse_anterior = pressionado

    # ---------- desenho ----------
    def _quad(self, x, y, w, h, cor):
        glBindTexture(GL_TEXTURE_2D, 0)
        glColor4f(*cor)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def _quad_textura(self, textura, x, y, w, h, alpha=1.0):
        if textura is None:
            return
        glBindTexture(GL_TEXTURE_2D, textura)
        glColor4f(1.0, 1.0, 1.0, alpha)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(x, y)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(x + w, y)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(x + w, y + h)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(x, y + h)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)

    def desenhar(self):
        if self.hud_oculto:
            return
        margem = self._margem()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, float(self.largura), float(self.altura), 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)

        # Linha compacta de FPS no canto superior esquerdo.
        if self._fps_tex is not None:
            tw, th = self._fps_tex_tamanho
            pad = self._px(0.003)
            self._quad(margem - pad, margem - pad, tw + 2 * pad, th + 2 * pad, _COR_FUNDO)
            self._quad_textura(self._fps_tex, margem, margem, tw, th)

        # Lista de controles (H) ou apenas a dica de uma linha no canto inferior.
        if self.mostrar_controles and self._controles_tex is not None:
            tw, th = self._controles_tex_tamanho
            pad = self._px(0.004)
            y = self.altura - margem - (th + 2 * pad)
            self._quad(margem - pad, y, tw + 2 * pad, th + 2 * pad, _COR_FUNDO)
            self._quad_textura(self._controles_tex, margem, y + pad, tw, th)
        elif self._dica_tex is not None:
            tw, th = self._dica_tex_tamanho
            pad = self._px(0.003)
            y = self.altura - margem - (th + 2 * pad)
            self._quad(margem - pad, y, tw + 2 * pad, th + 2 * pad, _COR_FUNDO)
            self._quad_textura(self._dica_tex, margem, y + pad, tw, th)

        # Botão "? Sobre" pequeno no canto superior direito (cor muda no hover).
        bx, by, bw, bh = self._sobre_botao_rect()
        cor = _COR_FUNDO_HOVER if self._sobre_hover else _COR_FUNDO_BOTOES
        self._quad(bx, by, bw, bh, cor)
        tw, th = self._sobre_botao_tex_tamanho
        self._quad_textura(self._sobre_botao_tex, bx + (bw - tw) / 2.0, by + (bh - th) / 2.0, tw, th)

        # Painel Sobre ao centro (a animação continua rodando por trás).
        if self.mostrar_sobre and self._sobre_tex is not None:
            px, py, pw, ph = self._sobre_painel_rect()
            self._quad(0, 0, self.largura, self.altura, _COR_VEU)
            self._quad(px, py, pw, ph, _COR_FUNDO)
            tw, th = self._sobre_tex_tamanho
            self._quad_textura(self._sobre_tex, px + (pw - tw) / 2.0, py + (ph - th) / 2.0, tw, th)
            fx, fy, fw, fh = self._fechar_rect()
            self._quad(fx, fy, fw, fh, _COR_FUNDO_FECHAR)
            tw, th = self._fechar_tex_tamanho
            self._quad_textura(self._fechar_tex, fx + (fw - tw) / 2.0, fy + (fh - th) / 2.0, tw, th)

        # Restaura o estado do pipeline para a cena no próximo quadro.
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
