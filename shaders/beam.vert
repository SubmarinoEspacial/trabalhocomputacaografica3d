#version 120

// gl_Vertex é a posição local no cone do feixe (eixo Y, centro na origem).
// gl_ModelViewProjectionMatrix leva o vértice do cone até a tela.
varying vec3 v_local_position;

void main() {
    v_local_position = gl_Vertex.xyz;
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
