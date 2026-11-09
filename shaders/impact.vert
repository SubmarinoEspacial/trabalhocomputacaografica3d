#version 120

// v_uv percorre o plano horizontal do anel entre 0 e 1.
varying vec2 v_uv;

void main() {
    v_uv = gl_MultiTexCoord0.xy;
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
