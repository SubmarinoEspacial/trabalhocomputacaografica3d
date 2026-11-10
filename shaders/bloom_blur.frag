#version 120

// Desfoque gaussiano separável executado no alvo de bloom (1/4 de resolução).
uniform sampler2D u_texture;
uniform vec2 u_texel;
uniform vec2 u_direction;
varying vec2 v_uv;

void main() {
    vec2 passo = u_texel * u_direction;
    vec3 cor = texture2D(u_texture, v_uv).rgb * 0.2270270270;
    cor += texture2D(u_texture, v_uv + passo * 1.0).rgb * 0.1945945946;
    cor += texture2D(u_texture, v_uv - passo * 1.0).rgb * 0.1945945946;
    cor += texture2D(u_texture, v_uv + passo * 2.0).rgb * 0.1216216216;
    cor += texture2D(u_texture, v_uv - passo * 2.0).rgb * 0.1216216216;
    cor += texture2D(u_texture, v_uv + passo * 3.0).rgb * 0.0540540541;
    cor += texture2D(u_texture, v_uv - passo * 3.0).rgb * 0.0540540541;
    cor += texture2D(u_texture, v_uv + passo * 4.0).rgb * 0.0162162162;
    cor += texture2D(u_texture, v_uv - passo * 4.0).rgb * 0.0162162162;
    gl_FragColor = vec4(cor, 1.0);
}
