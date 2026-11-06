#version 120

// gl_Vertex e a posicao local fornecida pela geometria no perfil compativel.
// gl_Normal e a normal do vertice/face; vertexUV e o (u,v) da imagem em cada vertice.
// A API imediata transporta vertexUV por gl_MultiTexCoord0.xy.
// gl_ModelViewMatrix, gl_ProjectionMatrix e gl_NormalMatrix sao built-ins.
// repeatUV e offsetUV controlam repeticao/deslocamento no espaco UV.
// u_light_view_projection_eye leva a posicao ao espaco do mapa da luz.
uniform vec2 repeatUV;
uniform vec2 offsetUV;
uniform mat4 u_light_view_projection_eye;
varying vec3 v_normal_eye;
varying vec3 v_position_eye;
varying vec2 v_uv;
varying vec4 v_shadow_position;

void main() {
    vec4 positionEye = gl_ModelViewMatrix * gl_Vertex;
    vec2 vertexUV = gl_MultiTexCoord0.xy;
    v_uv = vertexUV * repeatUV + offsetUV;
    v_normal_eye = normalize(gl_NormalMatrix * gl_Normal);
    v_position_eye = positionEye.xyz;
    v_shadow_position = u_light_view_projection_eye * positionEye;
    gl_Position = gl_ProjectionMatrix * positionEye;
}