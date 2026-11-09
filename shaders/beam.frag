#version 120

// Cor e intensidade do volume cônico do feixe.
uniform vec3 u_beam_color;
uniform float u_intensity;
// Tempo usado para animar o ruído e o cintilar do feixe.
uniform float u_time;
// Textura repetível de ruído que quebra a superfície lisa do cone.
uniform sampler2D u_noise_texture;
// Dimensões do cone: altura e raios nas extremidades.
uniform float u_height;
uniform float u_radius_bottom;
uniform float u_radius_top;
// Exposição e gamma alinham o feixe ao tonemapping da cena.
uniform float u_exposure;
uniform float u_gamma;
varying vec3 v_local_position;

void main() {
    // 0 na base inferior do cone e 1 no vértice junto ao disco.
    float vertical = clamp(v_local_position.y / u_height + 0.5, 0.0, 1.0);
    float radiusAt = mix(u_radius_bottom, u_radius_top, vertical);
    float radial = length(v_local_position.xz);

    // A borda radial suave evita um contorno duro no cone.
    float edge = 1.0 - smoothstep(
        max(radiusAt * 0.48, 0.005),
        radiusAt + 0.015,
        radial
    );
    float angle = atan(v_local_position.z, v_local_position.x) / 6.28318530718 + 0.5;
    vec2 noiseUV = vec2(angle * 1.8 + u_time * 0.03, vertical * 1.6 + u_time * 0.14);
    float noiseA = texture2D(u_noise_texture, noiseUV).r;
    float noiseB = texture2D(
        u_noise_texture,
        vec2(angle * 3.1 - u_time * 0.02, vertical * 2.4 - u_time * 0.09)
    ).r;
    float noise = 0.62 * noiseA + 0.38 * noiseB;

    float fade = smoothstep(0.0, 0.10, vertical) * (0.24 + 0.76 * vertical);
    float flicker = 0.88 + 0.12 * sin(u_time * 21.0 + vertical * 11.0);
    float alpha = u_intensity * edge * fade * flicker * (0.55 + 0.60 * noise);
    alpha = clamp(alpha, 0.0, 0.88);

    vec3 color = u_beam_color * (0.52 + 0.88 * noise);
    vec3 mapped = vec3(1.0) - exp(-max(color, vec3(0.0)) * u_exposure);
    gl_FragColor = vec4(
        pow(mapped, vec3(1.0 / max(u_gamma, 0.001))),
        alpha
    );
}
