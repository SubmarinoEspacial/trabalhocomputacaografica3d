"""Aplicação de validação da câmera e dos controles da cena de abdução."""
import gc
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework"))

# As checagens de erro do PyOpenGL custam caro por chamada GL; DEBUG_GL religa
# tudo em config.py quando for necessário depurar. Isto precisa vir antes de
# qualquer import de OpenGL.GL, pois o PyOpenGL lê as flags na importação.
import OpenGL

from src import config as C

if not C.DEBUG_GL:
    OpenGL.ERROR_CHECKING = False
    OpenGL.ERROR_LOGGING = False
    OpenGL.FULL_LOGGING = False

import pygame
from OpenGL.GL import (
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_RENDERER,
    GL_VERSION,
    glClearColor,
    glGetString,
    glLoadIdentity,
    glMatrixMode,
    glViewport,
)
from OpenGL.GLU import gluPerspective

from core.base import Base
from core.mesh import Mesh
from core_ext.scene import Scene
from src.controls.camera_rig import CameraRig
from src.entities.disco_voador import DiscoVoador
from src.entities.efeitos import EfeitosAbducao
from src.entities.submarino import Submarino
from src.environment.adaptive import QualidadeAdaptativa
from src.environment.foam import build_espuma
from src.environment.mar import build_mar
from src.environment.night_materials import NoiteLightingContext
from src.environment.point_light import PointLight
from src.environment.postprocess import PostProcess
from src.environment.shadow import ActionShadowMap
from src.environment.sky import build_ceu
from src.interaction.abducao import AbducaoController
from src.ui.hud import Hud
from light.directional import DirectionalLight
from light.ambient import AmbientLight


def setup_luz():
    """Cria a luz lunar direcional e o contexto Lambert da atmosfera noturna."""
    # O modelo difuso Lambert segue o conceito de iluminação do capítulo 6 do livro.
    # O shader recebe u_light_direction_eye, u_light_ambient e u_light_diffuse.
    # Cada material envia u_material_color e, no piso, u_use_texture/u_texture.
    # A normal perpendicular à face define o difuso pelo produto escalar com a luz.
    # Lambert controla brilho local; ShadowMap calcula a sombra projetada em outro passe.
    # A luz ambiente azulada simula o céu noturno; a direcional fria representa a lua.
    luzAmbiente = AmbientLight(color=C.AMBIENT_COLOR, strength=C.AMBIENT_STRENGTH)
    luzLunar = DirectionalLight(
        color=C.MOON_COLOR,
        strength=C.MOON_STRENGTH,
    )
    luzLunar.setDirection(C.MOON_DIRECTION)
    return NoiteLightingContext(
        luzLunar,
        luzAmbiente,
        fogColor=C.FOG_COLOR,
        fogStart=C.FOG_START,
        fogEnd=C.FOG_END,
        fogDensity=C.FOG_DENSITY,
        exposure=C.EXPOSURE,
        gamma=C.GAMMA,
    )


class Aplicacao(Base):
    """Controla a câmera, pausa e ciclo de vida da cena sobre a Base."""

    def initialize(self):
        """Cria a projeção, câmera, entidades e controlador da interação."""
        self._ultimo_tamanho_janela = (self.largura, self.altura)
        self._atualizar_projecao(self.largura, self.altura)
        glClearColor(*C.SKY_COLOR)
        self._preparar_perfilamento()

        self.lighting = setup_luz()
        self._criar_sombra()
        self.camera_rig = CameraRig()
        self.postprocess = PostProcess(self.largura, self.altura)
        self._criar_mundo()
        self.frame_limit = C.TARGET_FPS if self.hud.limitador_ativo else 0
        self.qualidade_adaptativa = QualidadeAdaptativa(self.postprocess)

        self.pausado = False
        self.tempoAnimacao = 0.0
        # Estado anterior de cada tecla de função (detecção de borda por quadro).
        self._pausa_anterior = False
        self._reset_anterior = False
        self._tempos_anterior = False
        self._apresentacao_anterior = False
        self._qualidade_baixa_anterior = False
        self._qualidade_media_anterior = False
        self._qualidade_alta_anterior = False
        self._qualidade_minima_anterior = False
        self._controles_anterior = False
        self._sobre_anterior = False
        self._limite_fps_anterior = False
        self._hud_anterior = False
        self._tela_cheia_anterior = False
        self._alt_enter_anterior = False
        self._alvo_fps_anterior = False
        self._adaptativo_anterior = False
        self._hud_refresh_pendente = False
        self._frames_perfil = 0
        self._ultima_impressao = time.perf_counter()
        self._acumulos = {
            "logica": 0.0,
            "arvore": 0.0,
            "sombra": 0.0,
            "principal": 0.0,
            "pos": 0.0,
            "hud": 0.0,
            "frame": 0.0,
        }
        self._mesh_draw_principal = 0.0
        self._mesh_draw_sombra = 0.0
        self._draw_principal = 0
        self._draw_sombra = 0
        self._tempo_hud = 0.0
        self._diag_estatico = {}
        self._gl_renderer, self._gl_version = self._ler_info_gl()
        print(
            f"GL_RENDERER: {self._gl_renderer} | GL_VERSION: {self._gl_version} | "
            f"janela {self.largura}x{self.altura}",
            flush=True,
        )
        self._proximo_gc = time.perf_counter() + C.GC_INTERVAL
        self._atualizar_titulo(False)
        # Congela o que já existe e desliga o GC automático no laço; a coleta
        # manual de _coletar_lixo evita acúmulo de ciclos sem pausas por frame.
        gc.collect()
        gc.freeze()
        gc.disable()

    @staticmethod
    def _ler_info_gl():
        """Lê o renderer/versão uma única vez para diagnóstico de hardware."""
        renderer = glGetString(GL_RENDERER)
        version = glGetString(GL_VERSION)
        decodificar = lambda valor: (
            valor.decode("utf-8", errors="replace") if isinstance(valor, bytes) else str(valor)
        )
        return decodificar(renderer or "?"), decodificar(version or "?")

    def _coletar_lixo(self):
        """GC automático fica desligado no laço; coleta manual a cada N segundos."""
        agora = time.perf_counter()
        if agora >= self._proximo_gc:
            gc.collect()
            self._proximo_gc = agora + C.GC_INTERVAL

    def on_resize(self, largura, altura):
        """Ajusta viewport, projeção e pós-processamento sem reiniciar a cena."""
        if largura <= 0 or altura <= 0:
            return
        if not pygame.display.is_fullscreen():
            self._ultimo_tamanho_janela = (largura, altura)
        self._atualizar_projecao(largura, altura)
        if hasattr(self, "postprocess"):
            self.postprocess.resize(largura, altura)
        if hasattr(self, "hud"):
            self.hud.on_resize(self.largura, self.altura)

    def on_escape(self):
        """ESC fecha o painel Sobre; senão sai da tela cheia. Nunca fecha o app."""
        if getattr(self, "hud", None) is not None and self.hud.sobre_aberto():
            self.hud.fechar_sobre()
            return False
        if pygame.display.is_fullscreen():
            self._alternar_tela_cheia()
        return False

    def _atualizar_projecao(self, largura, altura):
        """Recalcula viewport e aspect ratio mantendo o campo vertical."""
        self.largura = int(largura)
        self.altura = int(altura)
        glViewport(0, 0, self.largura, self.altura)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # O domo noturno tem raio 185; o far plane de 300 evita recortá-lo.
        gluPerspective(55.0, self.largura / self.altura, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)

    def _alternar_tela_cheia(self):
        """Alterna F11/Alt+Enter sem recriar recursos de GPU."""
        estava_cheia = pygame.display.is_fullscreen()
        if not estava_cheia:
            # Guarda exatamente o tamanho atual para restaurar ao sair.
            self._ultimo_tamanho_janela = (self.largura, self.altura)

        # Em SDL/Linux, toggle_fullscreen preserva a janela e o contexto OpenGL.
        pygame.display.toggle_fullscreen()
        largura, altura = pygame.display.get_window_size()

        if estava_cheia:
            # O SDL deveria restaurar a janela; se não o fizer, não recriamos a GPU.
            if (largura, altura) != self._ultimo_tamanho_janela:
                self.largura, self.altura = largura, altura
        self.largura, self.altura = int(largura), int(altura)
        self.on_resize(self.largura, self.altura)

    def _criar_sombra(self):
        """Cria a sombra lunar usando a resolução do perfil atual."""
        # O depth map acompanha a ação em vez de ficar preso ao centro do mundo.
        self.shadow_map = ActionShadowMap(
            self.lighting,
            resolution=C.SHADOW_RESOLUTION,
        )
        self.lighting.light.shadowMap = self.shadow_map
        self.lighting.light.shadowCamera = self.shadow_map.shadowCamera
        self.lighting.light.shadowMaterial = self.shadow_map.depthMaterial
        self.lighting.light.shadowRenderTarget = self.shadow_map.target

    def _criar_mundo(self):
        """Monta céu, água, modelos e efeitos conforme o perfil atual."""
        self.scene = Scene()
        # O céu entra primeiro no passe opaco para servir de fundo do horizonte.
        self.ceu = build_ceu(self.scene)
        self.water_material = build_mar(self.scene, self.lighting)

        self.submarino = Submarino()
        self.submarino.build(self.lighting)
        assert self.submarino.root is not None
        self.submarino.root.setCastShadow(True)
        self.submarino.root.setReceiveShadow(True)
        self.scene.add(self.submarino.root)
        self.disco = DiscoVoador()
        self.disco.build(self.lighting)
        assert self.disco.root is not None
        assert self.disco.feixe is not None
        self.disco.root.setCastShadow(True)
        self.disco.root.setReceiveShadow(True)
        self.disco.feixe.setCastShadow(False)
        self.disco.feixe.setReceiveShadow(False)
        self.scene.add(self.disco.root)
        # A espuma é adicionada depois da água para participar do passe transparente.
        self.espuma = build_espuma(self.scene)
        self.efeitos = EfeitosAbducao(self.scene)
        self.controlador = AbducaoController(self.submarino, self.disco)
        # HUD desenhado por último: não toca no passe de sombra nem na cena.
        self.hud = Hud(self.largura, self.altura)
        pygame.mouse.set_visible(True)

    def _selecionar_perfil_manual(self, nome):
        """Escolha manual (F3/F4/F5/X): fixa o perfil e desliga o adaptativo.

        Aplica na hora tudo o que o perfil controla por uniforms/flags
        (escala de render, PCF, ondas da água, luzes pontuais e bloom) e
        recria só o mapa de sombra quando a resolução muda (o tamanho do
        depth map é fixo no FBO). Grade da água e tesselação dos modelos
        não mudam em execução; valem no próximo arranque. Funciona com a
        animação pausada, com o HUD aberto e em tela cheia.
        """
        C.aplicar_perfil_qualidade(nome)
        if self.shadow_map.resolution != C.SHADOW_RESOLUTION:
            # Só o depth map é recriado; a cena e a malha da água não são tocadas.
            self._criar_sombra()
        if hasattr(self, "postprocess"):
            self.postprocess.set_render_scale(C.RENDER_SCALE)
        if hasattr(self, "qualidade_adaptativa"):
            # Manual = adaptativo desligado; a base volta ao degrau zero.
            self.qualidade_adaptativa.ativo = False
            self.qualidade_adaptativa.recarregar_base()
        rotulo = {
            "minima": "mínima",
            "baixa": "baixa",
            "media": "média",
            "alta": "alta",
        }.get(C.QUALITY, C.QUALITY)
        self.hud.mostrar_mensagem(f"Qualidade: {rotulo}")
        self._hud_refresh_pendente = True
        self._zerar_perfil()
        pygame.display.set_caption(f"Validacao OpenGL | Perfil {C.QUALITY} | F2 tempos")
        print(
            f"Qualidade: {rotulo} (manual) | adaptativo desligado (G religa)",
            flush=True,
        )

    def _preparar_perfilamento(self):
        """Ativa F2/`--profile` e mede o custo de Mesh.draw sem mudar a cena."""
        self.perfil_ativo = any(
            arg in ("--profile", "--perfilar") for arg in sys.argv[1:]
        )
        self._mesh_original_draw = Mesh.draw

        def draw_medido(mesh, render_pass=None):
            # Conta apenas desenhos reais (o filtro de passe fica no Mesh.draw).
            if render_pass == "shadow":
                if mesh.castShadow:
                    self._draw_sombra += 1
            else:
                transparente = getattr(mesh.material, "transparent", False)
                if (render_pass == "opaque" and not transparente) or (
                    render_pass == "transparent" and transparente
                ):
                    self._draw_principal += 1
            if not self.perfil_ativo:
                return self._mesh_original_draw(mesh, render_pass)
            inicio = time.perf_counter()
            try:
                return self._mesh_original_draw(mesh, render_pass)
            finally:
                gasto = time.perf_counter() - inicio
                if render_pass == "shadow":
                    self._mesh_draw_sombra += gasto
                else:
                    self._mesh_draw_principal += gasto

        # O corredor medido é texto; a cena e os passes continuam os mesmos.
        Mesh.draw = draw_medido

    def _contar_arvore(self):
        """Conta Meshes visíveis e geometria da água na hierarquia."""
        total_meshes = 0
        meshes_sombra = 0
        vertices_agua = 0
        indices_agua = 0
        pilha = [(self.scene, True)]
        while pilha:
            no, pai_visivel = pilha.pop()
            visivel = pai_visivel and no.visible
            if isinstance(no, Mesh) and visivel:
                total_meshes += 1
                if no.castShadow:
                    meshes_sombra += 1
                geometria = no.geometry
                segmentos_agua = getattr(geometria, "segments", None)
                if segmentos_agua is not None:
                    vertices_agua = max(
                        vertices_agua,
                        int(segmentos_agua) * int(segmentos_agua),
                    )
                    indices_agua = max(
                        indices_agua,
                        int(getattr(geometria, "vertex_count", 0)),
                    )
            if visivel:
                pilha.extend((filho, visivel) for filho in no.children)
        return total_meshes, meshes_sombra, vertices_agua, indices_agua

    def _atualizar_titulo(self, ativa):
        """Restaura ou aplica o sufixo de FPS no título da janela."""
        titulo = "Validacao OpenGL"
        if ativa:
            titulo += " | F2"
        pygame.display.set_caption(titulo)

    def _zerar_perfil(self):
        """Recomeça a média para a próxima leitura de F2."""
        self._frames_perfil = 0
        self._ultima_impressao = time.perf_counter()
        for chave in self._acumulos:
            self._acumulos[chave] = 0.0

    def _registrar_frame(self, tempos):
        """Acumula os tempos e mostra o diagnóstico a cada segundo."""
        self._frames_perfil += 1
        for chave, valor in tempos.items():
            self._acumulos[chave] += valor

        agora = time.perf_counter()
        intervalo = agora - self._ultima_impressao
        if intervalo < 1.0:
            return

        frames = max(1, self._frames_perfil)
        contadores = self._acumulos
        meshes, meshes_sombra, vertices_agua, indices_agua = self._contar_arvore()
        luzes = self.lighting.point_light_count + 2
        fps = frames / intervalo
        self._diag_estatico = {
            "meshes": meshes,
            "meshes_sombra": meshes_sombra,
            "agua_vtx": vertices_agua,
            "agua_idx": indices_agua,
            "luzes": luzes,
        }
        texto = (
            f"F2 {fps:.1f} | frame {contadores['frame'] / frames * 1000:.1f} ms | "
            f"logica {contadores['logica'] / frames * 1000:.2f} | "
            f"arvore {contadores['arvore'] / frames * 1000:.2f} | "
            f"sombra {contadores['sombra'] / frames * 1000:.2f} | "
            f"principal {contadores['principal'] / frames * 1000:.2f} | "
            f"pos {contadores['pos'] / frames * 1000:.2f} | "
            f"hud {contadores['hud'] / frames * 1000:.2f} | "
            f"draws principal={self._draw_principal} sombra={self._draw_sombra} | "
            f"Meshes cena={meshes} sombra={meshes_sombra} | luzes={luzes} | "
            f"agua_vtx={vertices_agua} idx={indices_agua} | "
            f"sombra={self.shadow_map.resolution}px PCF={C.SHADOW_PCF_SAMPLES} | "
            f"GL={self._gl_renderer} | janela={self.largura}x{self.altura}"
        )
        print(texto, flush=True)
        pygame.display.set_caption(f"Validacao OpenGL | {texto}")
        self._zerar_perfil()

    def _diagnostico_hud(self):
        """Resumo enviado ao HUD: hardware fixo + contadores do último quadro."""
        static = self._diag_estatico
        return {
            "renderer": self._gl_renderer,
            "version": self._gl_version,
            "janela": f"{self.largura}x{self.altura}",
            "sombra_res": self.shadow_map.resolution,
            "pcf": C.SHADOW_PCF_SAMPLES,
            "luzes": static.get("luzes", self.lighting.point_light_count + 2),
            "agua_vtx": static.get("agua_vtx", "?"),
            "meshes": static.get("meshes", "?"),
            "meshes_sombra": static.get("meshes_sombra", "?"),
            "draws_principal": self._draw_principal,
            "draws_sombra": self._draw_sombra,
        }

    def _atualizar_luzes_pontuais(self):
        """Posiciona os porões/holofote do sub e as luzes do disco a cada quadro.

        A conversão mundo->olho reutiliza a transformação de câmera do
        framework, na organização de luzes de Stemkoski e Pascale (2022, cap. 6).
        """
        sub = self.submarino
        disco = self.disco
        frente_x = math.cos(sub.yaw)
        frente_z = -math.sin(sub.yaw)
        escala = max(0.0, sub.scale)
        brilho_sub = min(1.0, escala * 1.4) * (0.70 + 0.30 * sub.glow)
        altura_disco = disco.position[1] + disco.hover_offset

        # Cores brancas centralizadas em LIGHT_COLOR; a força sobe com POINTLIGHT_INTENSITY.
        luzes = (
            PointLight(
                (
                    sub.position[0] + frente_x * 0.10 * escala,
                    sub.position[1] + 0.30 * escala,
                    sub.position[2] + frente_z * 0.10 * escala,
                ),
                C.LIGHT_COLOR,
                C.SUB_PORTHOLE_LIGHT_STRENGTH * C.POINTLIGHT_INTENSITY * brilho_sub,
                C.SUB_PORTHOLE_LIGHT_RANGE,
                enabled=sub.visible and brilho_sub > 0.02,
            ),
            PointLight(
                (
                    disco.position[0],
                    altura_disco - 1.35 * C.DISC_SCALE,
                    disco.position[2],
                ),
                C.LIGHT_COLOR,
                C.UFO_BEAM_LIGHT_STRENGTH * C.POINTLIGHT_INTENSITY * disco.beam_amount,
                C.UFO_BEAM_LIGHT_RANGE,
                enabled=disco.beam_amount > 0.01,
            ),
            PointLight(
                (
                    disco.position[0],
                    altura_disco + 0.10 * C.DISC_SCALE,
                    disco.position[2],
                ),
                C.LIGHT_COLOR,
                C.UFO_GLOW_LIGHT_STRENGTH * C.POINTLIGHT_INTENSITY,
                C.UFO_GLOW_LIGHT_RANGE,
                enabled=disco.root is not None and disco.root.visible,
            ),
            PointLight(
                (
                    sub.position[0] + frente_x * 0.90 * escala,
                    sub.position[1] + 1.05 * escala,
                    sub.position[2] + frente_z * 0.90 * escala,
                ),
                C.LIGHT_COLOR,
                C.SUB_SEARCHLIGHT_STRENGTH * C.POINTLIGHT_INTENSITY * brilho_sub,
                C.SUB_SEARCHLIGHT_RANGE,
                enabled=sub.visible and escala > 0.15,
            ),
        )
        self.lighting.set_point_lights(luzes, self.camera_rig)

    def update(self):
        """Atualiza controles e cena; renderiza mesmo quando a animação pausa."""
        # O delta real limita os saltos da animação se a máquina perder quadros.
        delta_quadro = min(self.deltaTime, 0.05)
        if self.largura <= 0 or self.altura <= 0:
            # Janela minimizada: mantemos o loop e o pausa, mas não desenhamos.
            return
        teclas = pygame.key.get_pressed()
        inicio_frame = time.perf_counter()

        pausa_pressionado = bool(teclas[C.KEYMAP["pausa"]])
        if pausa_pressionado and not self._pausa_anterior:
            self.pausado = not self.pausado
        self._pausa_anterior = pausa_pressionado

        reset_pressionado = bool(teclas[C.KEYMAP["reset"]])
        if reset_pressionado and not self._reset_anterior:
            self.controlador.reset()
            self.camera_rig.reset()
        self._reset_anterior = reset_pressionado

        apresentacao_pressionado = bool(teclas[C.KEYMAP["apresentacao"]])
        if apresentacao_pressionado and not self._apresentacao_anterior:
            C.PRESENT_MODE = 0 if C.PRESENT_MODE else 1
            estado = "ligado" if C.PRESENT_MODE else "desligado"
            print(f"Modo apresentação dos veículos: {estado} (L alterna)", flush=True)
        self._apresentacao_anterior = apresentacao_pressionado

        tempos_pressionado = bool(teclas[C.KEYMAP["tempos"]])
        if tempos_pressionado and not self._tempos_anterior:
            self.perfil_ativo = not self.perfil_ativo
            self._zerar_perfil()
            self._hud_refresh_pendente = True
            self._atualizar_titulo(self.perfil_ativo)
        self._tempos_anterior = tempos_pressionado

        hud_pressionado = bool(teclas[C.KEYMAP["hud"]])
        if hud_pressionado and not self._hud_anterior:
            oculto = self.hud.alternar_hud()
            print("HUD oculto (F1 mostra de novo)" if oculto else "HUD visível", flush=True)
        self._hud_anterior = hud_pressionado

        # F3/F4/F5/X fixam o perfil de qualidade (escolha manual; desliga o adaptativo).
        for acao, perfil in (
            ("qualidade_baixa", "baixa"),
            ("qualidade_media", "media"),
            ("qualidade_alta", "alta"),
            ("qualidade_minima", "minima"),
        ):
            pressionado = bool(teclas[C.KEYMAP[acao]])
            atributo = f"_{acao}_anterior"
            if pressionado and not getattr(self, atributo):
                self._selecionar_perfil_manual(perfil)
            setattr(self, atributo, pressionado)

        controles_pressionado = bool(teclas[C.KEYMAP["controles"]])
        if controles_pressionado and not self._controles_anterior:
            self.hud.alternar_controles()
        self._controles_anterior = controles_pressionado

        sobre_pressionado = bool(teclas[C.KEYMAP["sobre"]])
        if sobre_pressionado and not self._sobre_anterior:
            self.hud.alternar_sobre()
        self._sobre_anterior = sobre_pressionado

        limite_pressionado = bool(teclas[C.KEYMAP["limite_fps"]])
        if limite_pressionado and not self._limite_fps_anterior:
            ativo = self.hud.alternar_limite()
            self.frame_limit = C.TARGET_FPS if ativo else 0
            self._hud_refresh_pendente = True
            print(
                f"Limitador de FPS: {C.TARGET_FPS} FPS (clock.tick)"
                if ativo else "Limitador de FPS: sem limite",
                flush=True,
            )
        self._limite_fps_anterior = limite_pressionado

        alvo_pressionado = bool(teclas[C.KEYMAP["alvo_fps"]])
        if alvo_pressionado and not self._alvo_fps_anterior:
            C.TARGET_FPS = 120 if C.TARGET_FPS == 60 else 60
            if self.hud.limitador_ativo:
                self.frame_limit = C.TARGET_FPS
            self._hud_refresh_pendente = True
            print(f"Alvo de FPS: {C.TARGET_FPS} (T alterna 60/120)", flush=True)
        self._alvo_fps_anterior = alvo_pressionado

        adaptativo_pressionado = bool(teclas[C.KEYMAP["adaptativo"]])
        if adaptativo_pressionado and not self._adaptativo_anterior:
            ativo = self.qualidade_adaptativa.alternar()
            self._hud_refresh_pendente = True
            print(
                f"Qualidade adaptativa: {'ligada' if ativo else 'desligada'} "
                f"(G alterna; nível {self.qualidade_adaptativa.nivel})",
                flush=True,
            )
        self._adaptativo_anterior = adaptativo_pressionado

        tela_pressionado = bool(teclas[C.KEYMAP["tela_cheia"]])
        if tela_pressionado and not self._tela_cheia_anterior:
            self._alternar_tela_cheia()
        self._tela_cheia_anterior = tela_pressionado

        alt_pressionado = bool(pygame.key.get_mods() & C.KEYMAP["alt"])
        enter_pressionado = bool(
            teclas[C.KEYMAP["enter"]] or teclas[C.KEYMAP["enter_numerico"]]
        )
        alt_enter_pressionado = alt_pressionado and enter_pressionado
        if alt_enter_pressionado and not self._alt_enter_anterior:
            self._alternar_tela_cheia()
        self._alt_enter_anterior = alt_enter_pressionado

        # A câmera usa o tempo do quadro, inclusive enquanto a cena está pausada.
        self.camera_rig.update(delta_quadro, teclas)
        self.ceu.update(self.camera_rig)
        self.lighting.setCameraRotation(self.camera_rig.yaw, self.camera_rig.pitch)
        delta_logica = 0.0 if self.pausado else delta_quadro
        self.tempoAnimacao += delta_logica
        self.water_material.setTime(self.tempoAnimacao)

        inicio_logica = time.perf_counter()
        if self.submarino.root is not None:
            self.controlador.update(delta_logica, self.tempoAnimacao)
            self.submarino.apply(self.tempoAnimacao)
            self.espuma.update(self.submarino, self.tempoAnimacao)
        if self.disco.root is not None:
            self.disco.apply()
        self.efeitos.update(self.disco, self.tempoAnimacao)
        self._atualizar_luzes_pontuais()
        tempo_logica = time.perf_counter() - inicio_logica

        # O foco da sombra usa as posições lógicas, antes de desenhar a cena.
        self._mesh_draw_principal = 0.0
        self._mesh_draw_sombra = 0.0
        self._draw_principal = 0
        self._draw_sombra = 0
        inicio_sombra = time.perf_counter()
        self.shadow_map.updateFocus(delta_quadro, self.submarino, self.disco)
        self.shadow_map.render(self.scene, self.camera_rig)
        tempo_sombra = time.perf_counter() - inicio_sombra

        # A cena é desenhada em textura e depois recebe bloom/vinheta na janela.
        inicio_principal = time.perf_counter()
        self.postprocess.begin()
        self.camera_rig.apply()
        self.scene.render()
        tempo_principal = time.perf_counter() - inicio_principal

        inicio_pos = time.perf_counter()
        self.postprocess.end()
        tempo_pos = time.perf_counter() - inicio_pos
        tempo_arvore = max(0.0, tempo_principal - self._mesh_draw_principal)

        # O HUD vai por cima do pós-processamento, com FPS e estado atualizados.
        estado_nome = self.controlador.estado.name if self.controlador else "?"
        inicio_hud = time.perf_counter()
        forcar_refresh = self._hud_refresh_pendente
        self._hud_refresh_pendente = False
        self.hud.atualizar(
            self.deltaTime,
            estado_nome,
            timings={
                "logica": tempo_logica,
                "arvore": tempo_arvore,
                "sombra": tempo_sombra,
                "principal": tempo_principal,
                "pos": tempo_pos,
                "hud": self._tempo_hud,
            },
            perfil_ativo=self.perfil_ativo,
            diagnostico=self._diagnostico_hud() if self.perfil_ativo else None,
            alvo_fps=C.TARGET_FPS,
            qualidade=C.QUALITY,
            escala=C.RENDER_SCALE,
            adaptativo=self.qualidade_adaptativa.ativo,
            forcar_refresh=forcar_refresh,
        )
        self.hud.tratar_mouse(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])
        self.hud.desenhar()
        self._tempo_hud = time.perf_counter() - inicio_hud
        tempo_frame = time.perf_counter() - inicio_frame

        # A adaptação lê a média do HUD e troca escala/uniforms, nunca malhas.
        self.qualidade_adaptativa.update(self.deltaTime, self.hud.fps())
        self._coletar_lixo()

        if self.perfil_ativo:
            self._registrar_frame({
                "logica": tempo_logica,
                "arvore": tempo_arvore,
                "sombra": tempo_sombra,
                "principal": tempo_principal,
                "pos": tempo_pos,
                "hud": self._tempo_hud,
                "frame": tempo_frame,
            })


if __name__ == "__main__":
    Aplicacao(
        largura=C.WINDOW_SIZE[0],
        altura=C.WINDOW_SIZE[1],
        titulo="Validacao OpenGL",
        tamanho_minimo=C.MIN_WINDOW_SIZE,
    )
