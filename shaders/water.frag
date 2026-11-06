#version 120

// Direcao, cor difusa e ambiente da DirectionalLight/AmbientLight.
uniform vec3 u_light_direction_eye;
uniform vec3 u_light_ambient;
uniform vec3 u_light_diffuse;
// Cores da água, crista e neblina; alpha_base controla a transparência geral.
uniform vec3 u_water_color;
uniform vec3 u_sky_color;
uniform float u_water_alpha;
uniform float u_fog_start;
uniform float u_fog_end;
// Profundidade da luz, resolução em texels, bias e flags de sombra.
uniform sampler2D u_shadow_map;
uniform vec2 u_shadow_texel_size;
uniform float u_shadow_bias;
uniform int u_shadow_enabled;
uniform int u_receive_shadow;
varying vec3 v_normal_eye;
varying vec3 v_position_eye;
varying vec3 v_world_position;
varying float v_wave_height;
varying vec4 v_shadow_position;

void main() {
    vec3 normal = normalize(v_normal_eye);
    vec3 lightDirection = normalize(-u_light_direction_eye);
    vec3 viewDirection = normalize(-v_position_eye);
    float diffuse = max(dot(normal, lightDirection), 0.0);
    vec3 reflected = reflect(-lightDirection, normal);
    float specular = pow(max(dot(viewDirection, reflected), 0.0), 96.0);

    float shadow = 0.0;
    vec3 lightCoord = v_shadow_position.xyz / v_shadow_position.w;
    lightCoord = lightCoord * 0.5 + 0.5;
    if (u_shadow_enabled != 0 && u_receive_shadow != 0 &&
        lightCoord.x >= 0.0 && lightCoord.x <= 1.0 &&
        lightCoord.y >= 0.0 && lightCoord.y <= 1.0 &&
        lightCoord.z >= 0.0 && lightCoord.z <= 1.0) {
        float bias = max(u_shadow_bias * (1.0 - diffuse), u_shadow_bias * 0.35);
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                vec2 offset = vec2(float(x), float(y)) * u_shadow_texel_size;
                float depth = texture2D(u_shadow_map, lightCoord.xy + offset).r;
                shadow += lightCoord.z - bias > depth ? 1.0 : 0.0;
            }
        }
        shadow /= 9.0;
    }

    float fresnel = pow(1.0 - max(dot(normal, viewDirection), 0.0), 5.0);
    float crest = smoothstep(0.10, 0.32, v_wave_height);
    vec3 color = mix(u_water_color, u_sky_color, 0.16 + 0.42 * fresnel + 0.18 * crest);
    color *= u_light_ambient + u_light_diffuse * diffuse * (1.0 - 0.72 * shadow);
    color += vec3(1.0) * specular * (1.0 - shadow);

    // O fog mistura água distante com o céu no horizonte; água rasa mantém transparência.
    float fog = smoothstep(u_fog_start, u_fog_end, length(v_position_eye));
    color = mix(color, u_sky_color, fog);
    float alpha = clamp(u_water_alpha + 0.22 * fresnel, 0.0, 0.82);
    gl_FragColor = vec4(color, alpha);
}