#version 120

// v_uv cobre a tela inteira no quad final de pós-processamento.
varying vec2 v_uv;

void main() {
    v_uv = gl_MultiTexCoord0.xy;
    gl_Position = gl_Vertex;
}
