#version 120

// gl_Vertex é a posição do vértice na esfera unitária escalada para o domo.
// gl_Normal é a direção radial da esfera e representa a direção do céu.
// gl_ModelViewProjectionMatrix é a matriz built-in que leva o vértice à tela.
varying vec3 v_sky_direction;

void main() {
    // A normal radial não depende da escala do domo e serve como vetor de visada.
    v_sky_direction = normalize(gl_Normal);
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
