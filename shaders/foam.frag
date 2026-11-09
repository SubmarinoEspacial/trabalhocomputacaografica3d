#version 120

// Textura procedural de bolhas; a intensidade vem do canal vermelho.
uniform sampler2D u_foam_texture;
// Tempo acumulado e deslocamento das duas camadas de espuma.
uniform float u_time;
uniform vec2 u_scroll;
// Escala do UV, opacidade, cor e brilho da espuma.
uniform float u_scale;
uniform float u_alpha;
uniform vec3 u_foam_color;
uniform float u_brightness;
// 1 = máscara circular (contato); 0 = máscara retangular (esteira).
uniform float u_radial;
// Exposição e gamma alinham a espuma ao restante da cena.
uniform float u_exposure;
uniform float u_gamma;
varying vec2 v_uv;

void main() {
    // Duas leituras em escalas e direções diferentes quebram a repetição.
    vec2 uvA = v_uv * u_scale + u_scroll * u_time;
    vec2 uvB = v_uv * u_scale * 2.13 - u_scroll * u_time * 1.7;
    float foamA = texture2D(u_foam_texture, uvA).r;
    float foamB = texture2D(u_foam_texture, uvB).r;
    float foam = clamp(0.68 * foamA + 0.42 * foamB, 0.0, 1.0);

    // A borda suave evita que o quad apareça como um retângulo rígido.
    vec2 d = abs(v_uv - 0.5);
    float circular = 1.0 - smoothstep(0.28, 0.5, length(d));
    float rectangular = (1.0 - smoothstep(0.38, 0.5, d.y))
                      * smoothstep(0.0, 0.14, v_uv.x)
                      * (1.0 - smoothstep(0.86, 1.0, v_uv.x));
    float mask = mix(rectangular, circular, u_radial);
    float alpha = clamp(foam * mask * u_alpha, 0.0, 0.92);

    vec3 color = u_foam_color * (0.65 + 0.55 * foam) * u_brightness;
    vec3 mapped = vec3(1.0) - exp(-max(color, vec3(0.0)) * u_exposure);
    gl_FragColor = vec4(
        pow(mapped, vec3(1.0 / max(u_gamma, 0.001))),
        alpha
    );
}
