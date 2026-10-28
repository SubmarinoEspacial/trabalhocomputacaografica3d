"""Base mínima própria para validar a janela Pygame com contexto OpenGL.

Esta implementação provisória não é uma cópia nem substitui a classe Base do
framework de Stemkoski e Pascale (2022).
"""
import pygame
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, glClear, glEnable


class Base:
    """Cria a janela e executa o ciclo principal com delta time em segundos."""

    def __init__(self, largura=960, altura=640, titulo="Validacao OpenGL"):
        self.largura = largura
        self.altura = altura
        self.delta_time = 0.0
        self.executando = True

        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.set_mode(
            (self.largura, self.altura), pygame.DOUBLEBUF | pygame.OPENGL
        )
        pygame.display.set_caption(titulo)

        glEnable(GL_DEPTH_TEST)
        self.relogio = pygame.time.Clock()

        self.initialize()
        self.run()

    def initialize(self):
        """Prepara os recursos específicos da cena na classe derivada."""

    def update(self):
        """Atualiza e desenha um quadro na classe derivada."""
        raise NotImplementedError("A classe derivada deve implementar update().")

    def run(self):
        """Processa eventos e atualiza a cena até fechar a janela."""
        while self.executando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.executando = False
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.executando = False

            if not self.executando:
                break

            # O limite de quadros controla o uso de recursos; a animação usa o tempo medido.
            self.delta_time = self.relogio.tick(60) / 1000.0
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.update()
            pygame.display.flip()

        pygame.quit()