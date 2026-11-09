#version 120

// Cena renderizada no framebuffer de cor, amostrada na tela inteira.
uniform sampler2D u_scene_texture;
// Tamanho de um texel, usado para espalhar as amostras do bloom.
uniform vec2 u_texel_size;
// Intensidade do halo e limiar de brilho que alimenta o bloom.
uniform float u_bloom_strength;
uniform float u_bloom_threshold;
// u_bloom_enabled permite ao perfil baixo pular todas as amostras do halo.
uniform int u_bloom_enabled;
// Escurecimento suave das bordas e tinta fria do grade noturno.
uniform float u_vignette_strength;
uniform vec3 u_cool_tint;
varying vec2 v_uv;

// Extrai apenas a parte acima do limiar; luzes, lua e feixe geram o halo.
vec3 amostraBrilhante(vec2 uv) {
    vec3 cor = texture2D(u_scene_texture, uv).rgb;
    return max(cor - vec3(u_bloom_threshold), vec3(0.0));
}

void main() {
    vec3 color = texture2D(u_scene_texture, v_uv).rgb;
    vec2 t = u_texel_size;

    if (u_bloom_enabled != 0) {
        // Oito amostras próximas formam o núcleo do brilho e quatro distantes
        // espalham um halo suave sem exigir um segundo passe de desfoque.
        vec3 bloom =
            amostraBrilhante(v_uv + vec2( 4.0,  0.0) * t) +
            amostraBrilhante(v_uv + vec2(-4.0,  0.0) * t) +
            amostraBrilhante(v_uv + vec2( 0.0,  4.0) * t) +
            amostraBrilhante(v_uv + vec2( 0.0, -4.0) * t) +
            amostraBrilhante(v_uv + vec2( 3.0,  3.0) * t) +
            amostraBrilhante(v_uv + vec2(-3.0,  3.0) * t) +
            amostraBrilhante(v_uv + vec2( 3.0, -3.0) * t) +
            amostraBrilhante(v_uv + vec2(-3.0, -3.0) * t) +
            0.55 * amostraBrilhante(v_uv + vec2(10.0,  0.0) * t) +
            0.55 * amostraBrilhante(v_uv + vec2(-10.0, 0.0) * t) +
            0.55 * amostraBrilhante(v_uv + vec2( 0.0, 10.0) * t) +
            0.55 * amostraBrilhante(v_uv + vec2( 0.0, -10.0) * t);
        bloom /= 10.2;
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
