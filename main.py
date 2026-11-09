"""Aplicação de validação da câmera e dos controles da cena de abdução."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework"))

import pygame
from OpenGL.GL import (
    GL_MODELVIEW,
    GL_PROJECTION,
    glClearColor,
    glLoadIdentity,
    glMatrixMode,
    glViewport,
)
from OpenGL.GLU import gluPerspective

from core.base import Base
from core.mesh import Mesh
from core_ext.scene import Scene
from src.controls.camera_rig import MovementRig
from src import config as C
from src.entities.disco_voador import DiscoVoador
from src.entities.efeitos import EfeitosAbducao
from src.entities.submarino import Submarino
from src.environment.foam import build_espuma
from src.environment.mar import build_mar
from src.environment.night_materials import NoiteLightingContext
from src.environment.point_light import PointLight
from src.environment.postprocess import PostProcess
from src.environment.shadow import ActionShadowMap
from src.environment.sky import build_ceu
from src.interaction.abducao import AbducaoController
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
        self.camera_rig = MovementRig(posicao=(0.0, 13.0, 34.0))
        self.camera_rig.pitch = -17.0
        self.postprocess = PostProcess(self.largura, self.altura)
        self._criar_mundo()

        self.pausado = False
        self.tempoAnimacao = 0.0
        self._espaco_anterior = False
        self._r_anterior = False
        self._f3_anterior = False
        self._l_anterior = False
        self._f1_anterior = False
        self._f2_anterior = False
        self._f4_anterior = False
        self._f11_anterior = False
        self._alt_enter_anterior = False
        self._frames_perfil = 0
        self._ultima_impressao = time.perf_counter()
        self._acumulos = {
            "logica": 0.0,
            "arvore": 0.0,
            "sombra": 0.0,
            "principal": 0.0,
            "pos": 0.0,
            "frame": 0.0,
        }
        self._mesh_draw_principal = 0.0
        self._mesh_draw_sombra = 0.0
        self._atualizar_titulo(False)

    def on_resize(self, largura, altura):
        """Ajusta viewport, projeção e pós-processamento sem reiniciar a cena."""
        if largura <= 0 or altura <= 0:
            return
        if not pygame.display.is_fullscreen():
            self._ultimo_tamanho_janela = (largura, altura)
        self._atualizar_projecao(largura, altura)
        if hasattr(self, "postprocess"):
            self.postprocess.resize(largura, altura)

    def on_escape(self):
        """ESC sai da tela cheia; não fecha a aplicação."""
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

    def _trocar_perfil_qualidade(self, nome):
        """Aplica um perfil e recria sombra/cena com os novos parâmetros."""
        if nome == C.QUALITY:
            return
        C.aplicar_perfil_qualidade(nome)
        self._criar_sombra()
        self._criar_mundo()
        self.tempoAnimacao = 0.0
        self.pausado = False
        self._zerar_perfil()
        pygame.display.set_caption(
            f"Validacao OpenGL | Perfil {C.QUALITY} | F3 mostra o perfil"
        )

    def _preparar_perfilamento(self):
        """Ativa F3/`--profile` e mede o custo de Mesh.draw sem mudar a cena."""
        self.perfil_ativo = any(
            arg in ("--profile", "--perfilar") for arg in sys.argv[1:]
        )
        self._mesh_original_draw = Mesh.draw

        def draw_medido(mesh, render_pass=None):
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
            titulo += " | F3"
        pygame.display.set_caption(titulo)

    def _zerar_perfil(self):
        """Recomeça a média para a próxima leitura de F3."""
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
        texto = (
            f"F3 {fps:.1f} | frame {contadores['frame'] / frames * 1000:.1f} ms | "
            f"logica {contadores['logica'] / frames * 1000:.2f} | "
            f"arvore {contadores['arvore'] / frames * 1000:.2f} | "
            f"sombra {contadores['sombra'] / frames * 1000:.2f} | "
            f"principal {contadores['principal'] / frames * 1000:.2f} | "
            f"pos {contadores['pos'] / frames * 1000:.2f} | "
            f"Meshes cena={meshes} sombra={meshes_sombra} | luzes={luzes} | "
            f"agua_vtx={vertices_agua} idx={indices_agua} | sombra={self.shadow_map.resolution}px PCF={C.SHADOW_PCF_SAMPLES} | passes_pos=1"
        )
        print(texto)
        pygame.display.set_caption(f"Validacao OpenGL | {texto}")
        self._zerar_perfil()

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

        espaco_pressionado = bool(teclas[pygame.K_SPACE])
        if espaco_pressionado and not self._espaco_anterior:
            self.pausado = not self.pausado
        self._espaco_anterior = espaco_pressionado

        r_pressionado = bool(teclas[pygame.K_r])
        if r_pressionado and not self._r_anterior:
            self.controlador.reset()
        self._r_anterior = r_pressionado

        l_pressionado = bool(teclas[pygame.K_l])
        if l_pressionado and not self._l_anterior:
            C.PRESENT_MODE = 0 if C.PRESENT_MODE else 1
            estado = "ligado" if C.PRESENT_MODE else "desligado"
            print(f"Modo apresentação dos veículos: {estado} (L alterna)", flush=True)
        self._l_anterior = l_pressionado

        f3_pressionado = bool(teclas[pygame.K_F3])
        if f3_pressionado and not self._f3_anterior:
            self.perfil_ativo = not self.perfil_ativo
            self._zerar_perfil()
            self._atualizar_titulo(self.perfil_ativo)
        self._f3_anterior = f3_pressionado

        f1_pressionado = bool(teclas[pygame.K_F1])
        if f1_pressionado and not self._f1_anterior:
            self._trocar_perfil_qualidade("baixa")
        self._f1_anterior = f1_pressionado

        f2_pressionado = bool(teclas[pygame.K_F2])
        if f2_pressionado and not self._f2_anterior:
            self._trocar_perfil_qualidade("media")
        self._f2_anterior = f2_pressionado

        f4_pressionado = bool(teclas[pygame.K_F4])
        if f4_pressionado and not self._f4_anterior:
            self._trocar_perfil_qualidade("alta")
        self._f4_anterior = f4_pressionado

        f11_pressionado = bool(teclas[pygame.K_F11])
        if f11_pressionado and not self._f11_anterior:
            self._alternar_tela_cheia()
        self._f11_anterior = f11_pressionado

        alt_pressionado = bool(pygame.key.get_mods() & pygame.KMOD_ALT)
        enter_pressionado = bool(teclas[pygame.K_RETURN] or teclas[pygame.K_KP_ENTER])
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
        tempo_frame = time.perf_counter() - inicio_frame
        tempo_arvore = max(0.0, tempo_principal - self._mesh_draw_principal)

        if self.perfil_ativo:
            self._registrar_frame({
                "logica": tempo_logica,
                "arvore": tempo_arvore,
                "sombra": tempo_sombra,
                "principal": tempo_principal,
                "pos": tempo_pos,
                "frame": tempo_frame,
            })


if __name__ == "__main__":
    Aplicacao(
        largura=C.WINDOW_SIZE[0],
        altura=C.WINDOW_SIZE[1],
        titulo="Validacao OpenGL",
        tamanho_minimo=C.MIN_WINDOW_SIZE,
    )
