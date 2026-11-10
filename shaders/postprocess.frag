#version 120

// Cena renderizada no framebuffer de cor, amostrada na tela inteira.
uniform sampler2D u_scene_texture;
// Bloom já extraído e desfocado em 1/4 de resolução pelo passe dedicado.
uniform sampler2D u_bloom_texture;
// Intensidade do halo e chave para pular a amostra no perfil baixo.
uniform float u_bloom_strength;
uniform int u_bloom_enabled;
// Escurecimento suave das bordas e tinta fria do grade noturno.
uniform float u_vignette_strength;
uniform vec3 u_cool_tint;
varying vec2 v_uv;

void main() {
    vec3 color = texture2D(u_scene_texture, v_uv).rgb;

    if (u_bloom_enabled != 0) {
        // Uma única amostra no alvo reduzido substitui as 12 amostras em tela
        // cheia do passe antigo; o desfoque largo acontece no alvo de 1/4.
        vec3 bloom = texture2D(u_bloom_texture, v_uv).rgb;
        color += bloom * u_cool_tint * u_bloom_strength;
    }

    // Grade frio discreto preserva a leitura noturna sem lavar as cores das luzes.
    color = mix(color, color * u_cool_tint, 0.06);

    // A vinheta fecha as bordas e conduz o olhar ao feixe no centro.
    vec2 centro = v_uv * 2.0 - 1.0;
    float vinheta = clamp(
        1.0 - u_vignette_strength * 0.34 * dot(centro, centro),
        0.0,
        1.0
    );
    gl_FragColor = vec4(color * vinheta, 1.0);
}
