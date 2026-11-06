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
        self.castShadow = False
        self.receiveShadow = False
        self.children = []

    def add(self, *objects):
        """Adiciona nós filhos para compor a hierarquia da cena."""
        self.children.extend(objects)
        return self

    def setPosition(self, x, y, z):
        """Alias camelCase para atualizar a posição sem remover a API existente."""
        self.position = (x, y, z)

    def setRotation(self, x, y, z):
        """Alias camelCase para atualizar os ângulos Euler do nó."""
        self.rotation = (x, y, z)

    def setScale(self, x, y, z):
        """Alias camelCase para atualizar a escala do nó."""
        self.scale = (x, y, z)

    def setCastShadow(self, state=True):
        """Define se este ramo participa do passe de profundidade da luz."""
        self.castShadow = bool(state)
        for child in self.children:
            child.setCastShadow(state)

    def setReceiveShadow(self, state=True):
        """Define se este ramo recebe o teste de profundidade da sombra."""
        self.receiveShadow = bool(state)
        for child in self.children:
            child.setReceiveShadow(state)

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