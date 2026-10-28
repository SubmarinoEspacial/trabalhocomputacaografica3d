"""Geometrias simples criadas para a cena de testes."""
import math

from OpenGL.GL import (
    GL_QUADS,
    GL_TRIANGLE_FAN,
    glBegin,
    glEnd,
    glNormal3f,
    glTexCoord2f,
    glVertex3f,
)


class PlaneGeometry:
    """Plano horizontal com coordenadas UV configuráveis para repetição."""

    def __init__(self, width, depth, uv_repeat=(1.0, 1.0)):
        self.width = width
        self.depth = depth
        self.uv_repeat = uv_repeat

    def draw(self):
        """Repete o UV por quantidade de ladrilhos, mantendo proporção física."""
        half_width = self.width / 2.0
        half_depth = self.depth / 2.0
        repeat_u, repeat_v = self.uv_repeat
        vertices = (
            ((-half_width, 0.0, -half_depth), (0.0, 0.0)),
            ((-half_width, 0.0, half_depth), (0.0, repeat_v)),
            ((half_width, 0.0, half_depth), (repeat_u, repeat_v)),
            ((half_width, 0.0, -half_depth), (repeat_u, 0.0)),
        )

        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        for position, uv in vertices:
            glTexCoord2f(*uv)
            glVertex3f(*position)
        glEnd()


class BoxGeometry:
    """Caixa centrada na origem, formada por seis faces quadriláteras."""

    def __init__(self, width, height, depth):
        self.half_width = width / 2.0
        self.half_height = height / 2.0
        self.half_depth = depth / 2.0

    def draw(self):
        """Emite as seis faces da caixa com normais voltadas para fora."""
        x, y, z = self.half_width, self.half_height, self.half_depth
        faces = (
            ((0.0, 0.0, 1.0), ((-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z))),
            ((0.0, 0.0, -1.0), ((x, -y, -z), (-x, -y, -z), (-x, y, -z), (x, y, -z))),
            ((1.0, 0.0, 0.0), ((x, -y, z), (x, -y, -z), (x, y, -z), (x, y, z))),
            ((-1.0, 0.0, 0.0), ((-x, -y, -z), (-x, -y, z), (-x, y, z), (-x, y, -z))),
            ((0.0, 1.0, 0.0), ((-x, y, z), (x, y, z), (x, y, -z), (-x, y, -z))),
            ((0.0, -1.0, 0.0), ((-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z))),
        )
        face_uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

        glBegin(GL_QUADS)
        for normal, vertices in faces:
            glNormal3f(*normal)
            for position, uv in zip(vertices, face_uvs):
                glTexCoord2f(*uv)
                glVertex3f(*position)
        glEnd()


class CylinderGeometry:
    """Cilindro ao longo do eixo Y, criado para composição de modelos locais."""

    def __init__(self, radius_top, radius_bottom, height, segments=20):
        self.radius_top = radius_top
        self.radius_bottom = radius_bottom
        self.height = height
        self.segments = max(3, segments)

    def draw(self):
        """Desenha a lateral e fecha as duas bases com normais simples."""
        half_height = self.height / 2.0

        glBegin(GL_QUADS)
        for index in range(self.segments):
            angle_a = 2.0 * math.pi * index / self.segments
            angle_b = 2.0 * math.pi * (index + 1) / self.segments
            middle = (angle_a + angle_b) / 2.0
            glNormal3f(math.cos(middle), 0.0, math.sin(middle))
            for angle, y, radius in (
                (angle_a, -half_height, self.radius_bottom),
                (angle_b, -half_height, self.radius_bottom),
                (angle_b, half_height, self.radius_top),
                (angle_a, half_height, self.radius_top),
            ):
                glVertex3f(radius * math.cos(angle), y, radius * math.sin(angle))
        glEnd()

        for y, radius, normal_y in (
            (half_height, self.radius_top, 1.0),
            (-half_height, self.radius_bottom, -1.0),
        ):
            glBegin(GL_TRIANGLE_FAN)
            glNormal3f(0.0, normal_y, 0.0)
            glVertex3f(0.0, y, 0.0)
            indices = range(self.segments + 1)
            if normal_y < 0.0:
                indices = reversed(tuple(indices))
            for index in indices:
                angle = 2.0 * math.pi * index / self.segments
                glVertex3f(radius * math.cos(angle), y, radius * math.sin(angle))
            glEnd()