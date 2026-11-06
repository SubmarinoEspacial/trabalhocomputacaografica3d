#version 120

// Direcao dos raios, ambiente e difuso da luz direcional no espaco do olho.
uniform vec3 u_light_direction_eye;
uniform vec3 u_light_ambient;
uniform vec3 u_light_diffuse;
// Cor-base, alpha de blending e contribuicao emissiva independente da luz.
uniform vec3 u_material_color;
uniform float u_material_alpha;
uniform vec3 u_emissive_color;
uniform float u_emissive_strength;
// u_material_specular e u_material_shininess definem o highlight Phong.
uniform vec3 u_material_specular;
uniform float u_material_shininess;
// u_texture (sampler2D) consulta a imagem na coordenada interpolada v_uv.
// u_use_texture permite reutilizar este shader por materiais sem imagem.
uniform int u_use_texture;
uniform sampler2D u_texture;
// Map de profundidade, tamanho do texel, bias e flag de recepcao de sombra.
uniform sampler2D u_shadow_map;
uniform vec2 u_shadow_texel_size;
uniform float u_shadow_bias;
uniform int u_shadow_enabled;
// u_receive_shadow e enviado por cada Mesh; castShadow e filtrado no passe 1.
uniform int u_receive_shadow;
// Uniforms da neblina linear do fundo marinho; a cor coincide com o clear color do céu.
uniform vec3 u_fog_color;
uniform float u_fog_start;
uniform float u_fog_end;
varying vec3 v_normal_eye;
varying vec3 v_position_eye;
varying vec2 v_uv;
varying vec4 v_shadow_position;

void main() {
    vec3 baseColor = u_material_color;
    if (u_use_texture != 0) {
        baseColor *= texture2D(u_texture, v_uv).rgb;
    }

    vec3 normal = normalize(v_normal_eye);
    vec3 lightDirection = normalize(-u_light_direction_eye);
    float diffuse = max(dot(normal, lightDirection), 0.0);
    // Usamos Phong: a normal interpolada e normalizada e a luz avaliada aqui por fragmento.
    // Flat usa uma normal por face; Gouraud calcula a luz nos vertices; Phong interpola normais.
    vec3 viewDirection = normalize(-v_position_eye);
    vec3 reflectedDirection = reflect(-lightDirection, normal);
    float specular = u_material_shininess > 1.0
        ? pow(max(dot(viewDirection, reflectedDirection), 0.0), u_material_shininess)
        : 0.0;

    float shadow = 0.0;
    vec3 lightCoord = v_shadow_position.xyz / v_shadow_position.w;
    lightCoord = lightCoord * 0.5 + 0.5;
    if (u_shadow_enabled != 0 && u_receive_shadow != 0 &&
        lightCoord.x >= 0.0 && lightCoord.x <= 1.0 &&
        lightCoord.y >= 0.0 && lightCoord.y <= 1.0 &&
        lightCoord.z >= 0.0 && lightCoord.z <= 1.0) {
        float bias = max(u_shadow_bias * (1.0 - diffuse), u_shadow_bias * 0.2);
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                vec2 offset = vec2(float(x), float(y)) * u_shadow_texel_size;
                float closestDepth = texture2D(u_shadow_map, lightCoord.xy + offset).r;
                shadow += lightCoord.z - bias > closestDepth ? 1.0 : 0.0;
            }
        }
        shadow /= 9.0;
    }

    vec3 ambientTerm = baseColor * u_light_ambient;
    vec3 directTerm = baseColor * diffuse + u_material_specular * specular;
    vec3 color = ambientTerm + u_light_diffuse * directTerm * (1.0 - 0.72 * shadow);
    float fogAmount = smoothstep(u_fog_start, u_fog_end, length(v_position_eye));
    color = mix(color, u_fog_color, fogAmount);
    gl_FragColor = vec4(color + u_emissive_color * u_emissive_strength, u_material_alpha);
}