"""Geometrias planas e cúbicas para a cena de testes."""
from OpenGL.GL import GL_QUADS, glBegin, glEnd, glNormal3f, glTexCoord2f, glVertex3f


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