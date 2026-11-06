"""Raiz da hierarquia de objetos renderizáveis."""
from OpenGL.GL import (
    GL_BLEND,
    GL_BLEND_DST_ALPHA,
    GL_BLEND_DST_RGB,
    GL_BLEND_SRC_ALPHA,
    GL_BLEND_SRC_RGB,
    GL_DEPTH_WRITEMASK,
    GL_FALSE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TRUE,
    glBlendFunc,
    glBlendFuncSeparate,
    glDepthMask,
    glDisable,
    glEnable,
    glGetBooleanv,
    glGetIntegerv,
    glIsEnabled,
)

from core.object3d import Object3D


class Scene(Object3D):
    """Agrupa os objetos de uma cena sem aplicar transformação adicional."""

    def render(self, shadow_pass=False):
        """Desenha opacos, depois transparentes; depth pass ignora blending."""
        if shadow_pass:
            super().render("shadow")
            return

        super().render("opaque")
        blend_previo = bool(glIsEnabled(GL_BLEND))
        depth_write_previo = bool(glGetBooleanv(GL_DEPTH_WRITEMASK))
        fatores_blend = (
            int(glGetIntegerv(GL_BLEND_SRC_RGB)),
            int(glGetIntegerv(GL_BLEND_DST_RGB)),
            int(glGetIntegerv(GL_BLEND_SRC_ALPHA)),
            int(glGetIntegerv(GL_BLEND_DST_ALPHA)),
        )

        # Mantém depth test para o feixe ser ocultado por objetos opacos,
        # mas desliga depth writes para a transparência não bloquear a cena.
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        try:
            # O feixe e o unico transparente atual; todo opaco ja foi desenhado.
            super().render("transparent")
        finally:
            glDepthMask(GL_TRUE if depth_write_previo else GL_FALSE)
            glBlendFuncSeparate(*fatores_blend)
            if not blend_previo:
                glDisable(GL_BLEND)