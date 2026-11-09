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
// Uniforms da neblina do fundo marinho; a cor coincide com o horizonte do céu.
uniform vec3 u_fog_color;
uniform float u_fog_start;
uniform float u_fog_end;
// Densidade extra da neblina noturna, aplicada em conjunto com a faixa linear.
uniform float u_fog_density;
// Exposição e gamma finais aproximam a cena noturna do comportamento de uma câmera.
uniform float u_exposure;
uniform float u_gamma;
// Quatro luzes pontuais dinâmicas: posição/cor no espaço do olho e alcance no mundo.
uniform int u_point_light_count;
uniform vec3 u_point_light_position_eye[4];
uniform vec3 u_point_light_color[4];
uniform float u_point_light_range[4];
varying vec3 v_normal_eye;
varying vec3 v_position_eye;
varying vec2 v_uv;
varying vec4 v_shadow_position;

// Soma a contribuição de uma luz pontual com atenuação quadrática no alcance.
void acumularLuzPontual(
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
    float brilho = u_material_shininess > 1.0
        ? pow(max(dot(normal, meio), 0.0), u_material_shininess)
        : 0.0;
    difusa += corLuz * ndl * atenuacao;
    especular += corLuz * brilho * atenuacao;
}

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
        // PCF 5x5: 25 comparações suavizam a borda serrilhada do depth map.
        float bias = max(u_shadow_bias * (1.0 - diffuse), u_shadow_bias * 0.2);
        for (int x = -2; x <= 2; x++) {
            for (int y = -2; y <= 2; y++) {
                vec2 offset = vec2(float(x), float(y)) * u_shadow_texel_size;
                float closestDepth = texture2D(u_shadow_map, lightCoord.xy + offset).r;
                shadow += lightCoord.z - bias > closestDepth ? 1.0 : 0.0;
            }
        }
        shadow /= 25.0;
    }

    vec3 ambientTerm = baseColor * u_light_ambient;
    vec3 directTerm = baseColor * diffuse + u_material_specular * specular;
    vec3 color = ambientTerm + u_light_diffuse * directTerm * (1.0 - 0.72 * shadow);

    // As luzes pontuais não projetam sombra, mas iluminam casco, disco e detalhes.
    vec3 pointDiffuse = vec3(0.0);
    vec3 pointSpecular = vec3(0.0);
    if (u_point_light_count > 0) {
        acumularLuzPontual(
            u_point_light_position_eye[0], u_point_light_color[0],
            u_point_light_range[0], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    if (u_point_light_count > 1) {
        acumularLuzPontual(
            u_point_light_position_eye[1], u_point_light_color[1],
            u_point_light_range[1], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    if (u_point_light_count > 2) {
        acumularLuzPontual(
            u_point_light_position_eye[2], u_point_light_color[2],
            u_point_light_range[2], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    if (u_point_light_count > 3) {
        acumularLuzPontual(
            u_point_light_position_eye[3], u_point_light_color[3],
            u_point_light_range[3], normal, v_position_eye, viewDirection,
            pointDiffuse, pointSpecular
        );
    }
    color += baseColor * pointDiffuse + u_material_specular * pointSpecular;
    color += u_emissive_color * u_emissive_strength;

    // A neblina combina a faixa linear didática do projeto com uma densidade
    // exponencial, que fecha o horizonte noturno sem apagar os objetos próximos.
    float distancia = length(v_position_eye);
    float neblinaLinear = smoothstep(u_fog_start, u_fog_end, distancia);
    float neblinaDensa = 1.0 - exp(-pow(u_fog_density * distancia, 2.0));
    float fogAmount = clamp(max(neblinaLinear, neblinaDensa), 0.0, 1.0);
    color = mix(color, u_fog_color, fogAmount);

    // Tone mapping exponencial evita saturação e o gamma clareia as meias-luzes.
    vec3 mapped = vec3(1.0) - exp(-max(color, vec3(0.0)) * u_exposure);
    gl_FragColor = vec4(
        pow(mapped, vec3(1.0 / max(u_gamma, 0.001))),
        u_material_alpha
    );
}