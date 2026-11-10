"""Base mínima própria para validar a janela Pygame com contexto OpenGL.

Esta implementação provisória não é uma cópia nem substitui a classe Base do
framework de Stemkoski e Pascale (2022).
"""
import pygame
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, glClear, glEnable


class Base:
    """Cria a janela e executa o ciclo principal com delta time em segundos."""

    def __init__(
        self,
        largura=960,
        altura=640,
        titulo="Validacao OpenGL",
        tamanho_minimo=(640, 360),
    ):
        self.largura = largura
        self.altura = altura
        self.tamanho_minimo = tuple(tamanho_minimo)
        self.delta_time = 0.0
        self.executando = True

        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        # RESIZABLE delega ao SDL os eventos de arrastar bordas sem recriar a janela.
        pygame.display.set_mode(
            (self.largura, self.altura),
            pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.OPENGL,
        )
        pygame.display.set_caption(titulo)

        glEnable(GL_DEPTH_TEST)
        self.relogio = pygame.time.Clock()
        # Limitador de FPS público: o HUD alterna entre FRAME_LIMIT (60) e 0
        # (clock.tick(0) = sem limite) com a tecla V, para medir a capacidade real.
        # O VSync não é recriado aqui — set_mode não pediu vsync, então só o
        # clock.tick é alternável em tempo de execução.
        self.frame_limit = 60

        self.initialize()
        self.run()

    @property
    def deltaTime(self):
        """Alias camelCase usado pela aplicação, preservando delta_time."""
        return self.delta_time

    @deltaTime.setter
    def deltaTime(self, value):
        self.delta_time = value

    def on_resize(self, largura, altura):
        """Ponto de extensão para ajustar viewport, projeção e render targets."""

    def on_escape(self):
        """Devolve True quando ESC deve fechar; a aplicação pode interceptar ESC."""
        return True

    def _forcar_tamanho_minimo(self, largura, altura):
        """Limita a janela ao mínimo sem recriar o contexto OpenGL.

        A API privada `pygame._sdl2.video.Window` é usada apenas para impor o
        mínimo no SDL; se ela não existir nesta versão, o código apenas
        prossegue com o tamanho informado.
        """
        minimo_largura, minimo_altura = self.tamanho_minimo
        if largura >= minimo_largura and altura >= minimo_altura:
            return largura, altura
        try:
            from pygame._sdl2.video import Window
            janela = Window.from_display_module()
            janela.size = self.tamanho_minimo
            return self.tamanho_minimo
        except Exception:
            return max(largura, self.tamanho_minimo[0]), max(altura, self.tamanho_minimo[1])

    def _processar_redimensionamento(self, largura, altura):
        """Atualiza os tamanhos conhecidos e avisa a aplicação uma única vez."""
        largura, altura = int(largura), int(altura)
        if largura <= 0 or altura <= 0:
            self.largura = 0
            self.altura = 0
            return False
        largura, altura = self._forcar_tamanho_minimo(largura, altura)
        self.largura = largura
        self.altura = altura
        self.on_resize(largura, altura)
        return True

    def initialize(self):
        """Prepara os recursos específicos da cena na classe derivada."""

    def update(self):
        """Atualiza e desenha um quadro na classe derivada."""
        raise NotImplementedError("A classe derivada deve implementar update().")

    def run(self):
        """Processa eventos e atualiza a cena até fechar a janela."""
        janela_redimensionada = getattr(pygame, "WINDOWRESIZED", None)
        while self.executando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.executando = False
                elif evento.type == pygame.VIDEORESIZE:
                    # O SDL avisa o tamanho solicitado; a aplicação atualiza viewport/projeção.
                    self._processar_redimensionamento(evento.w, evento.h)
                elif janela_redimensionada is not None and evento.type == janela_redimensionada:
                    # Em algumas plataformas o evento não carrega w/h; lemos o tamanho real.
                    self._processar_redimensionamento(*pygame.display.get_window_size())
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    if self.on_escape():
                        self.executando = False

            if not self.executando:
                break

            # O limite de quadros controla o uso de recursos; a animação usa o tempo medido.
            self.deltaTime = self.relogio.tick(self.frame_limit) / 1000.0
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.update()
            pygame.display.flip()

        pygame.quit()