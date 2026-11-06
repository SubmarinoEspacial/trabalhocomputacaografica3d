"""Hierarquia gráfica mínima escrita para este projeto.

Implementação própria, sem cópia de código do livro; organiza os nós conforme
o conceito de Scene Graph Framework, capítulo 4, de Stemkoski e Pascale (2022).
"""
from OpenGL.GL import (
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glScalef,
    glTranslatef,
)


class Object3D:
    """Nó transformável que desenha a si mesmo e percorre seus filhos."""

    def __init__(self, position=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
        self.position = tuple(position)
        self.rotation = tuple(rotation)
        self.scale = tuple(scale)
        self.visible = True
        self.children = []

    def add(self, *objects):
        """Adiciona nós filhos para compor a hierarquia da cena."""
        self.children.extend(objects)
        return self

    def render(self, render_pass=None):
        """Aplica a transformação local e encaminha o passe pela hierarquia."""
        if not self.visible:
            return

        glPushMatrix()
        try:
            glTranslatef(*self.position)
            glRotatef(self.rotation[0], 1.0, 0.0, 0.0)
            glRotatef(self.rotation[1], 0.0, 1.0, 0.0)
            glRotatef(self.rotation[2], 0.0, 0.0, 1.0)
            glScalef(*self.scale)
            self.draw(render_pass)
            for child in self.children:
                child.render(render_pass)
        finally:
            glPopMatrix()

    def draw(self, render_pass=None):
        """Ponto de extensão para a geometria de cada nó."""