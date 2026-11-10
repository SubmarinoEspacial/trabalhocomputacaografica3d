"""Geometrias com normais planas por face e normais suaves na esfera.

BoxGeometry/CylinderGeometry/ConeGeometry enviam normais de face; SphereGeometry
envia normais radiais por vertice, interpoladas para o calculo Phong por fragmento.
"""
import math
import ctypes
import numpy as np

from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FLOAT,
    GL_QUADS,
    GL_TRIANGLES,
    GL_TRIANGLE_FAN,
    GL_STATIC_DRAW,
    GL_UNSIGNED_INT,
    GL_VERTEX_ARRAY,
    GL_NORMAL_ARRAY,
    GL_TEXTURE_COORD_ARRAY,
    GL_COMPILE,
    glBindBuffer,
    glBegin,
    glBufferData,
    glCallList,
    glDeleteLists,
    glEnd,
    glEndList,
    glGenLists,
    glNewList,
    glDrawElements,
    glEnableClientState,
    glDisableClientState,
    glGenBuffers,
    glNormal3f,
    glTexCoord2f,
    glNormalPointer,
    glVertexPointer,
    glTexCoordPointer,
    glVertex3f,
)


class _GeometriaLista:
    """Compila a emissão imediata uma única vez em uma display list.

    As geometrias pequenas eram reemitidas com milhares de chamadas Python por
    quadro (math.cos/sin + glVertex). A display list preserva o desenho e o
    estilo didático do código, mas elimina esse custo de CPU em tempo de execução.
    """

    _lista = None

    def draw(self):
        """Reaproveita a lista compilada; compila na primeira vez que desenha."""
        if self._lista is None:
            lista = glGenLists(1)
            glNewList(lista, GL_COMPILE)
            try:
                self._emitir()
            finally:
                glEndList()
            self._lista = lista
        glCallList(self._lista)

    def _emitir(self):
        raise NotImplementedError("A geometria deve implementar _emitir().")

    def __del__(self):
        lista = getattr(self, "_lista", None)
        if lista is not None:
            try:
                glDeleteLists(lista, 1)
            except Exception:
                pass  # contexto já destruído no encerramento do processo


class PlaneGeometry(_GeometriaLista):
    """Plano horizontal com coordenadas UV configuráveis para repetição."""

    def __init__(self, width, depth):
        self.width = width
        self.depth = depth

    def _emitir(self):
        """Repete o UV por quantidade de ladrilhos, mantendo proporção física."""
        half_width = self.width / 2.0
        half_depth = self.depth / 2.0
        vertices = (
            ((-half_width, 0.0, -half_depth), (0.0, 0.0)),
            ((-half_width, 0.0, half_depth), (0.0, 1.0)),
            ((half_width, 0.0, half_depth), (1.0, 1.0)),
            ((half_width, 0.0, -half_depth), (1.0, 0.0)),
        )

        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        for position, uv in vertices:
            glTexCoord2f(*uv)
            glVertex3f(*position)
        glEnd()


class WaterGridGeometry:
    """Grade indexada em VBO; cada vértice carrega posição, normal e UV."""

    def __init__(self, width, depth, segments=200):
        self.width = width
        self.depth = depth
        self.segments = max(2, segments)
        eixo_x = np.linspace(-width / 2.0, width / 2.0, self.segments, dtype=np.float32)
        eixo_z = np.linspace(-depth / 2.0, depth / 2.0, self.segments, dtype=np.float32)
        grid_x, grid_z = np.meshgrid(eixo_x, eixo_z)
        vertices = np.zeros((self.segments * self.segments, 8), dtype=np.float32)
        vertices[:, 0] = grid_x.reshape(-1)
        vertices[:, 2] = grid_z.reshape(-1)
        vertices[:, 4] = 1.0
        vertices[:, 6] = np.linspace(0.0, 1.0, self.segments, dtype=np.float32).repeat(self.segments)
        vertices[:, 7] = np.tile(
            np.linspace(0.0, 1.0, self.segments, dtype=np.float32), self.segments
        )

        indices = []
        for row in range(self.segments - 1):
            for column in range(self.segments - 1):
                lower_left = row * self.segments + column
                lower_right = lower_left + 1
                upper_left = lower_left + self.segments
                upper_right = upper_left + 1
                indices.extend((lower_left, upper_left, upper_right, lower_left, upper_right, lower_right))
        self.indices = np.asarray(indices, dtype=np.uint32)
        self.vertex_count = self.indices.size

        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def draw(self):
        """Emite a grade estática; o shader desloca altura e normal em GPU."""
        stride = 8 * np.dtype(np.float32).itemsize
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glVertexPointer(3, GL_FLOAT, stride, ctypes.c_void_p(0))
        glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(12))
        glTexCoordPointer(2, GL_FLOAT, stride, ctypes.c_void_p(24))
        glDrawElements(GL_TRIANGLES, self.vertex_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)


class BoxGeometry(_GeometriaLista):
    """Caixa centrada na origem, formada por seis faces quadriláteras."""

    def __init__(self, width, height, depth):
        self.half_width = width / 2.0
        self.half_height = height / 2.0
        self.half_depth = depth / 2.0

    def _emitir(self):
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


class CylinderGeometry(_GeometriaLista):
    """Cilindro ao longo do eixo Y, criado para composição de modelos locais."""

    def __init__(self, radius_top, radius_bottom, height, segments=20):
        self.radius_top = radius_top
        self.radius_bottom = radius_bottom
        self.height = height
        self.segments = max(3, segments)

    def _emitir(self):
        """Desenha lateral e bases; a normal inclui a inclinação do tronco."""
        half_height = self.height / 2.0
        # O raio varia com Y nos cones, então a normal lateral também tem componente Y.
        componente_y = (self.radius_bottom - self.radius_top) / self.height
        comprimento_normal = math.sqrt(1.0 + componente_y * componente_y)

        glBegin(GL_QUADS)
        for index in range(self.segments):
            angle_a = 2.0 * math.pi * index / self.segments
            angle_b = 2.0 * math.pi * (index + 1) / self.segments
            middle = (angle_a + angle_b) / 2.0
            glNormal3f(
                math.cos(middle) / comprimento_normal,
                componente_y / comprimento_normal,
                math.sin(middle) / comprimento_normal,
            )
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


class SphereGeometry(_GeometriaLista):
    """Esfera de raio unitário, escalada no nó Mesh para formar os modelos."""

    def __init__(self, segments=24, rings=16):
        self.segments = max(3, segments)
        self.rings = max(2, rings)

    def _emitir(self):
        """Tesselaciona a esfera em quadriláteros com normais suaves."""
        glBegin(GL_QUADS)
        for ring in range(self.rings):
            latitude_a = -math.pi / 2.0 + math.pi * ring / self.rings
            latitude_b = -math.pi / 2.0 + math.pi * (ring + 1) / self.rings
            for segment in range(self.segments):
                longitude_a = 2.0 * math.pi * segment / self.segments
                longitude_b = 2.0 * math.pi * (segment + 1) / self.segments
                for latitude, longitude in (
                    (latitude_a, longitude_a),
                    (latitude_a, longitude_b),
                    (latitude_b, longitude_b),
                    (latitude_b, longitude_a),
                ):
                    normal_x = math.cos(latitude) * math.cos(longitude)
                    normal_y = math.sin(latitude)
                    normal_z = math.cos(latitude) * math.sin(longitude)
                    glNormal3f(normal_x, normal_y, normal_z)
                    glVertex3f(normal_x, normal_y, normal_z)
        glEnd()


class ConeGeometry(_GeometriaLista):
    """Cone no eixo Y, com vértice em cima e base circular embaixo."""

    def __init__(self, radius=1.0, height=1.0, segments=24):
        self.radius = radius
        self.height = height
        self.segments = max(3, segments)

    def _emitir(self):
        """Desenha a lateral triangular e uma base voltada para baixo."""
        half_height = self.height / 2.0
        normal_length = math.hypot(self.height, self.radius)

        glBegin(GL_TRIANGLES)
        for segment in range(self.segments):
            angle_a = 2.0 * math.pi * segment / self.segments
            angle_b = 2.0 * math.pi * (segment + 1) / self.segments
            angle_middle = (angle_a + angle_b) / 2.0
            glNormal3f(
                self.height * math.cos(angle_middle) / normal_length,
                self.radius / normal_length,
                self.height * math.sin(angle_middle) / normal_length,
            )
            glVertex3f(self.radius * math.cos(angle_a), -half_height, self.radius * math.sin(angle_a))
            glVertex3f(self.radius * math.cos(angle_b), -half_height, self.radius * math.sin(angle_b))
            glVertex3f(0.0, half_height, 0.0)
        glEnd()

        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, -half_height, 0.0)
        for segment in range(self.segments, -1, -1):
            angle = 2.0 * math.pi * segment / self.segments
            glVertex3f(self.radius * math.cos(angle), -half_height, self.radius * math.sin(angle))
        glEnd()