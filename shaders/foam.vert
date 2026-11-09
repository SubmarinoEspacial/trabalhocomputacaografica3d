#version 120

// gl_Vertex é a posição da malha horizontal de espuma em espaço local.
// gl_MultiTexCoord0.xy é o UV unitário fornecido por PlaneGeometry.
// gl_ModelViewProjectionMatrix leva a posição até o clip space.
varying vec2 v_uv;

void main() {
    v_uv = gl_MultiTexCoord0.xy;
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
