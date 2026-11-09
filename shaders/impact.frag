#version 120

// Cor do anel de energia e intensidade global controlada pelo estado da abdução.
uniform vec3 u_impact_color;
uniform float u_amount;
// Tempo da animação usado para expandir as ondas concêntricas.
uniform float u_time;
// Exposição e gamma mantêm o efeito alinhado ao tone mapping da cena.
uniform float u_exposure;
uniform float u_gamma;
varying vec2 v_uv;

void main() {
    // Converte o UV para um raio normalizado: 0 no centro e 1 na borda do plano.
    vec2 centered = v_uv * 2.0 - 1.0;
    float radius = length(centered);

    // Duas frentes de onda defasadas expandem continuamente a partir do centro.
    float phaseA = fract(u_time * 0.58);
    float phaseB = fract(u_time * 0.58 + 0.48);
    float ringA = exp(-pow((radius - phaseA * 0.92) / 0.070, 2.0)) * (1.0 - phaseA);
    float ringB = exp(-pow((radius - phaseB * 0.92) / 0.060, 2.0)) * (1.0 - phaseB);
    float core = exp(-pow(radius / 0.24, 2.0));
    float edgeFade = 1.0 - smoothstep(0.78, 1.0, radius);

    float alpha = (0.62 * ringA + 0.42 * ringB + 0.55 * core)
        * edgeFade * clamp(u_amount, 0.0, 1.0);
    alpha = clamp(alpha, 0.0, 0.85);

    vec3 color = mix(u_impact_color, vec3(0.92, 0.98, 1.0), core * 0.55);
    color *= 1.0 + 0.45 * (ringA + ringB);
    vec3 mapped = vec3(1.0) - exp(-max(color, vec3(0.0)) * u_exposure);
    gl_FragColor = vec4(
        pow(mapped, vec3(1.0 / max(u_gamma, 0.001))),
        alpha
    );
}
