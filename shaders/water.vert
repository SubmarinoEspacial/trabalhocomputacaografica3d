#version 120

// gl_Vertex.xy/z fornece a grade; gl_Normal existe, mas a normal da água é analítica.
// gl_MultiTexCoord0.xy é vertexUV da grade (mantido para atributos da geometria padrão).
// gl_ModelViewMatrix/ProjectionMatrix e built-ins; os uniforms de onda vêm de config.py.
uniform float u_time;
uniform float u_water_level;
uniform vec4 u_wave0;
uniform float u_wave_speed0;
uniform vec4 u_wave1;
uniform float u_wave_speed1;
uniform vec4 u_wave2;
uniform float u_wave_speed2;
// Duas ondas menores de detalhe, também espelhadas em water_height/water_slope.
uniform vec4 u_wave3;
uniform float u_wave_speed3;
uniform vec4 u_wave4;
uniform float u_wave_speed4;
uniform mat4 u_light_view_projection_eye;
varying vec3 v_normal_eye;
varying vec3 v_position_eye;
varying vec3 v_world_position;
varying float v_wave_height;
varying vec4 v_shadow_position;

void main() {
    vec2 xz = gl_Vertex.xz;
    float phase0 = u_wave0.w * dot(u_wave0.xy, xz) + u_wave_speed0 * u_time;
    float phase1 = u_wave1.w * dot(u_wave1.xy, xz) + u_wave_speed1 * u_time;
    float phase2 = u_wave2.w * dot(u_wave2.xy, xz) + u_wave_speed2 * u_time;
    float phase3 = u_wave3.w * dot(u_wave3.xy, xz) + u_wave_speed3 * u_time;
    float phase4 = u_wave4.w * dot(u_wave4.xy, xz) + u_wave_speed4 * u_time;

    float waveHeight = u_wave0.z * sin(phase0)
                     + u_wave1.z * sin(phase1)
                     + u_wave2.z * sin(phase2)
                     + u_wave3.z * sin(phase3)
                     + u_wave4.z * sin(phase4);
    float derivativeX = u_wave0.z * u_wave0.w * u_wave0.x * cos(phase0)
                      + u_wave1.z * u_wave1.w * u_wave1.x * cos(phase1)
                      + u_wave2.z * u_wave2.w * u_wave2.x * cos(phase2)
                      + u_wave3.z * u_wave3.w * u_wave3.x * cos(phase3)
                      + u_wave4.z * u_wave4.w * u_wave4.x * cos(phase4);
    float derivativeZ = u_wave0.z * u_wave0.w * u_wave0.y * cos(phase0)
                      + u_wave1.z * u_wave1.w * u_wave1.y * cos(phase1)
                      + u_wave2.z * u_wave2.w * u_wave2.y * cos(phase2)
                      + u_wave3.z * u_wave3.w * u_wave3.y * cos(phase3)
                      + u_wave4.z * u_wave4.w * u_wave4.y * cos(phase4);

    vec3 displacedPosition = vec3(gl_Vertex.x, waveHeight, gl_Vertex.z);
    vec3 normalWorld = normalize(vec3(-derivativeX, 1.0, -derivativeZ));
    vec4 positionEye = gl_ModelViewMatrix * vec4(displacedPosition, 1.0);

    v_normal_eye = normalize(gl_NormalMatrix * normalWorld);
    v_position_eye = positionEye.xyz;
    v_world_position = vec3(gl_Vertex.x, u_water_level + waveHeight, gl_Vertex.z);
    v_wave_height = waveHeight;
    v_shadow_position = u_light_view_projection_eye * positionEye;
    gl_Position = gl_ProjectionMatrix * positionEye;
}