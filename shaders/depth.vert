#version 120

void main() {
    // gl_Vertex e a posicao local fornecida por cada geometria via glVertex.
    // gl_ModelViewProjectionMatrix e o uniform built-in da luz: projecao ortografica
    // * view da luz * modelo atual da hierarquia. gl_Position e o clip-space resultante.
    // O shader nao declara uniforms nem atributos personalizados.
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}