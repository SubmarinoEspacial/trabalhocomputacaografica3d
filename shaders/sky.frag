#version 120

// Cores lineares do gradiente: zênite, horizonte e parte abaixo do horizonte.
uniform vec3 u_sky_zenith;
uniform vec3 u_sky_horizon;
uniform vec3 u_sky_ground;
// Intensidade global das estrelas e textura equirretangular do céu.
uniform float u_star_intensity;
uniform sampler2D u_stars;
// Direção dos raios lunares; a lua aparece no sentido oposto.
uniform vec3 u_moon_direction;
// Cor, raio angular em radianos e textura em disco da lua.
uniform vec3 u_moon_color;
uniform float u_moon_angular_radius;
uniform sampler2D u_moon_texture;
// Exposição e gamma compartilham o tonemapping dos materiais da cena.
uniform float u_exposure;
uniform float u_gamma;
varying vec3 v_sky_direction;

void main() {
    vec3 direction = normalize(v_sky_direction);
    float altitude = direction.y;

    // O gradiente é mais escuro no zênite e clareia no horizonte.
    vec3 color = mix(
        u_sky_horizon,
        u_sky_zenith,
        pow(clamp(altitude, 0.0, 1.0), 0.55)
    );
    color = mix(u_sky_ground, color, smoothstep(-0.16, 0.015, altitude));

    // A textura equirretangular é consultada por longitude/latitude da direção.
    vec2 starUV = vec2(
        atan(direction.z, direction.x) / 6.28318530718 + 0.5,
        asin(clamp(direction.y, -1.0, 1.0)) / 3.14159265359 + 0.5
    );
    vec3 stars = texture2D(u_stars, starUV).rgb;
    stars *= u_star_intensity * smoothstep(-0.02, 0.10, altitude);
    color += stars;

    // A lua fica no sentido oposto à direção dos raios da DirectionalLight.
    vec3 moonCenter = normalize(-u_moon_direction);
    float angle = acos(clamp(dot(direction, moonCenter), -1.0, 1.0));
    float bevel = max(u_moon_angular_radius * 0.025, 0.0001);
    float disc = 1.0 - smoothstep(
        u_moon_angular_radius - bevel,
        u_moon_angular_radius + bevel,
        angle
    );

    // Base tangente no plano da lua para mapear a textura circular no disco.
    vec3 reference = abs(moonCenter.y) > 0.95
        ? vec3(1.0, 0.0, 0.0)
        : vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(reference, moonCenter));
    vec3 up = cross(moonCenter, right);
    float radiusSin = max(sin(u_moon_angular_radius), 0.0001);
    vec2 moonUV = vec2(dot(direction, right), dot(direction, up)) / radiusSin;
    vec3 moon = texture2D(u_moon_texture, moonUV * 0.5 + 0.5).rgb;

    // Halo atmosférico suave, mais largo que o disco lunar.
    float halo = exp(-pow(angle / (u_moon_angular_radius * 3.0), 2.0)) * 0.10
               + exp(-pow(angle / (u_moon_angular_radius * 8.0), 2.0)) * 0.035;
    color += u_moon_color * (moon * disc * 2.0 + halo);

    // O mesmo tone mapping e gamma dos materiais mantém o horizonte contínuo.
    vec3 mapped = vec3(1.0) - exp(-max(color, vec3(0.0)) * u_exposure);
    gl_FragColor = vec4(
        pow(mapped, vec3(1.0 / max(u_gamma, 0.001))),
        1.0
    );
}
