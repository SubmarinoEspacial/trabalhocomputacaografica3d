#version 120

// Extrai o brilho da cena em um alvo reduzido (1/4 de resolução).
uniform sampler2D u_scene_texture;
uniform vec2 u_source_texel;
uniform float u_threshold;
varying vec2 v_uv;

void main() {
    // Média 2x2 funciona como downsample suave ao reduzir para 1/4.
    vec2 t = u_source_texel * 0.5;
    vec3 cor = texture2D(u_scene_texture, v_uv + vec2(-t.x, -t.y)).rgb;
    cor += texture2D(u_scene_texture, v_uv + vec2( t.x, -t.y)).rgb;
    cor += texture2D(u_scene_texture, v_uv + vec2(-t.x,  t.y)).rgb;
    cor += texture2D(u_scene_texture, v_uv + vec2( t.x,  t.y)).rgb;
    cor *= 0.25;
    gl_FragColor = vec4(max(cor - vec3(u_threshold), vec3(0.0)), 1.0);
}
