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
// Densidade da neblina noturna, exposição e gamma compartilhados com materiais.
uniform float u_fog_density;
uniform float u_exposure;
uniform float u_gamma;
// Tempo da animação usado para deslocar as camadas de espuma.
uniform float u_time;
// Textura procedural de espuma, escala no mundo e intensidade das cristas.
uniform sampler2D u_foam_texture;
uniform float u_foam_scale;
uniform float u_foam_strength;
// Intensidade do brilho lunar amplo e do glitter fino nas ondas.
uniform float u_specular_strength;
// Profundidade da luz, resolução em texels, bias e flags de sombra.
uniform sampler2D u_shadow_map;
uniform vec2 u_shadow_texel_size;
uniform float u_shadow_bias;
// u_shadow_enabled liga o recebimento; u_pcf_samples escolhe 1, 4 ou 9 amostras.
uniform int u_shadow_enabled;
uniform int u_receive_shadow;
uniform int u_pcf_samples;
// Quatro luzes pontuais dinâmicas, já convertidas para o espaço do olho.
uniform int u_point_light_count;
uniform vec3 u_point_light_position_eye[4];
uniform vec3 u_point_light_color[4];
uniform float u_point_light_range[4];
varying vec3 v_normal_eye;
varying vec3 v_position_eye;
varying vec3 v_world_position;
varying float v_wave_height;
varying vec4 v_shadow_position;

// Compara a profundidade atual com a do shadow map para os modos de PCF.
float comparar_profundidade(vec2 uv, float z, float bias) {
    float maisProximo = texture2D(u_shadow_map, uv).r;
    return z - bias > maisProximo ? 1.0 : 0.0;
}

// Atenuação quadrática e brilho pontual usados pelo feixe e pelas luzes do sub.
void acumularLuzPontualAgua(
    vec3 posicaoLuz,
    vec3 corLuz,
    float alcance,
    vec3 normal,
    vec3 posicaoFragmento,
    vec3 direcaoVisao,
    inout vec3 difusa,
    inout vec3 especular
) {
    vec3 ateLuz = posicaoLuz - posicaoFragmento;
    float distancia = length(ateLuz);
    float atenuacao = clamp(1.0 - distancia / max(alcance, 0.001), 0.0, 1.0);
    atenuacao *= atenuacao;
    if (atenuacao <= 0.0001) {
        return;
    }

    vec3 direcaoLuz = ateLuz / max(distancia, 0.0001);
    float ndl = max(dot(normal, direcaoLuz), 0.0);
    vec3 meio = normalize(direcaoLuz + direcaoVisao);
    float brilho = pow(max(dot(normal, meio), 0.0), 110.0);
    difusa += corLuz * ndl * atenuacao;
    especular += corLuz * brilho * atenuacao;
}

void main() {
    vec3 normal = normalize(v_normal_eye);
    vec3 lightDirection = normalize(-u_light_direction_eye);
    vec3 viewDirection = normalize(-v_position_eye);
    float diffuse = max(dot(normal, lightDirection), 0.0);
    vec3 reflected = reflect(-lightDirection, normal);
    float specular = pow(max(dot(viewDirection, reflected), 0.0), 90.0);
    // Dois expoentes separam o brilho largo da lua dos pontos cintilantes.
    float glitter = pow(max(dot(viewDirection, reflected), 0.0), 420.0);

    float shadow = 0.0;
    vec3 lightCoord = v_shadow_position.xyz / v_shadow_position.w;
    lightCoord = lightCoord * 0.5 + 0.5;
    if (u_shadow_enabled != 0 && u_receive_shadow != 0 &&
        lightCoord.x >= 0.0 && lightCoord.x <= 1.0 &&
        lightCoord.y >= 0.0 && lightCoord.y <= 1.0 &&
        lightCoord.z >= 0.0 && lightCoord.z <= 1.0) {
        // O perfil escolhe entre centro (1), dois eixos (4) e uma grade 3x3 (9).
        float bias = max(u_shadow_bias * (1.0 - diffuse), u_shadow_bias * 0.35);
        if (u_pcf_samples <= 1) {
            shadow = comparar_profundidade(lightCoord.xy, lightCoord.z, bias);
        } else if (u_pcf_samples <= 4) {
            vec2 meioTexel = u_shadow_texel_size * 0.5;
            shadow += comparar_profundidade(lightCoord.xy + vec2(-meioTexel.x, -meioTexel.y), lightCoord.z, bias);
            shadow += comparar_profundidade(lightCoord.xy + vec2( meioTexel.x, -meioTexel.y), lightCoord.z, bias);
            shadow += comparar_profundidade(lightCoord.xy + vec2(-meioTexel.x,  meioTexel.y), lightCoord.z, bias);
            shadow += comparar_profundidade(lightCoord.xy + vec2( meioTexel.x,  meioTexel.y), lightCoord.z, bias);
            shadow /= 4.0;
        } else {
            for (int x = -1; x <= 1; x++) {
                for (int y = -1; y <= 1; y++) {
                    vec2 offset = vec2(float(x), float(y)) * u_shadow_texel_size;
                    shadow += comparar_profundidade(lightCoord.xy + offset, lightCoord.z, bias);
                }
            }
            shadow /= 9.0;
        }
    }

    float fresnel = pow(1.0 - max(dot(normal, viewDirection), 0.0), 5.0);
    float crest = smoothstep(0.10, 0.32, v_wave_height);
    vec3 color = mix(u_water_color, u_sky_color, 0.10 + 0.48 * fresnel + 0.12 * crest);
    color *= u_light_ambient + u_light_diffuse * diffuse * (1.0 - 0.72 * shadow);
    color += u_light_diffuse * (0.30 * specular + 1.10 * glitter)
           * u_specular_strength * (1.0 - shadow);

    // O feixe e as luzes do sub criam poças coloridas e reflexos pontuais na água.
    vec3 pointDiffuse = vec3(0.0);
    vec3 pointSpecular = vec3(0.0);
    if (u_point_light_count > 0) {
        acumularLuzPontualAgua(
            u_point_light_position_eye[0], u_point_light_color[0],
            u_point_light_range[0], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    if (u_point_light_count > 1) {
        acumularLuzPontualAgua(
            u_point_light_position_eye[1], u_point_light_color[1],
            u_point_light_range[1], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    if (u_point_light_count > 2) {
        acumularLuzPontualAgua(
            u_point_light_position_eye[2], u_point_light_color[2],
            u_point_light_range[2], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    if (u_point_light_count > 3) {
        acumularLuzPontualAgua(
            u_point_light_position_eye[3], u_point_light_color[3],
            u_point_light_range[3], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    color += u_water_color * pointDiffuse * 1.45 + pointSpecular * 1.10;

    // A espuma nasce nas cristas e é modulada por duas camadas da textura.
    vec2 foamUV = v_world_position.xz * u_foam_scale;
    float foamA = texture2D(
        u_foam_texture,
        foamUV + vec2(u_time * 0.018, -u_time * 0.012)
    ).r;
    float foamB = texture2D(
        u_foam_texture,
        foamUV * 2.15 + vec2(-u_time * 0.031, u_time * 0.023)
    ).r;
    float foamNoise = 0.65 * foamA + 0.35 * foamB;
    float crestMask = smoothstep(0.16, 0.42, v_wave_height + 0.06 * foamNoise);
    float foamMask = clamp(crestMask * foamNoise * 1.35 * u_foam_strength, 0.0, 1.0);
    color = mix(color, vec3(0.72, 0.84, 0.92), foamMask * 0.62);

    // O fog combina a faixa linear com a densidade noturna e mistura a água
    // distante com o horizonte; perto da câmera a transparência é preservada.
    float distancia = length(v_position_eye);
    float neblinaLinear = smoothstep(u_fog_start, u_fog_end, distancia);
    float neblinaDensa = 1.0 - exp(-pow(u_fog_density * distancia, 2.0));
    float fog = clamp(max(neblinaLinear, neblinaDensa), 0.0, 1.0);
    color = mix(color, u_sky_color, fog);

    // O mesmo tone mapping do material sólido mantém o horizonte contínuo.
    vec3 mapped = vec3(1.0) - exp(-max(color, vec3(0.0)) * u_exposure);
    float alpha = clamp(u_water_alpha + 0.22 * fresnel + 0.12 * foamMask, 0.0, 0.94);
    gl_FragColor = vec4(
        pow(mapped, vec3(1.0 / max(u_gamma, 0.001))),
        alpha
    );
}