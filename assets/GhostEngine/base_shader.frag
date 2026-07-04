#version 330 core

uniform vec3 uViewPos;
uniform sampler2D uTexture;
uniform vec2 uTileData;

uniform bool uDisableLighting;

in vec3 vNormal;
in vec3 vWorldPos;
in vec2 vTexCoord;

out vec4 FragColor;

struct PointLight {
    vec4 position;
    vec4 color;
    float range;
};

layout(std140) uniform PointLightBlock {
    PointLight pointLights[64];
};

uniform int uNumPointLights;

struct SpotLight {
    vec4 position; // w: intensity
    vec4 direction;
    vec4 color;
    vec3 config; // x: outer angle, y: inner angle, z: range
};

layout(std140) uniform SpotLightBlock {
    SpotLight spotLights[64];
};

uniform int uNumSpotLights;

vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
{
    float intensity = light.position.w;
    float distance_ = length(light.position.xyz - fragPos) / light.range;
    float rangeFade = pow(1.0 - clamp(distance_, 0.0, 1.0), 3.0);

    float facing = dot(normalize(normal), light.position.xyz - fragPos);
    facing = clamp(facing, 0.0, 1.0);

    vec3 color = light.color.rgb / vec3(255.0) * intensity;
    return (color * rangeFade) * facing;
}

vec3 rotateVectorByQuaternion(vec3 v, vec4 q) {
    vec3 temp = cross(q.xyz, v) + q.w * v;
    return v + 2.0 * cross(q.xyz, temp);
}

vec3 CalcSpotLight(SpotLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
{
    vec3 offset_normal = normalize(light.position.xyz - fragPos);
    float theta = dot(normalize(-light.direction.xyz), offset_normal);

    float innerCut = light.config.x;
    float outerCut = light.config.y;
    float epsilon  = innerCut - outerCut;

    float intensity = clamp((theta - outerCut) / max(epsilon, 0.001), 0.0, 1.0) * light.position.w;

    float distance_ = length(light.position.xyz - fragPos) / light.config.z;
    float rangeFade = pow(1.0 - clamp(distance_, 0.0, 1.0), 3.0);

    float facing = dot(normalize(normal), light.position.xyz - fragPos);
    facing = clamp(facing, 0.0, 1.0);

    vec3 color = light.color.rgb / vec3(255.0) * intensity;
    return (color * rangeFade) * facing;
}

void main()
{
    vec3 normal  = normalize(vNormal);
    vec3 viewDir = normalize(uViewPos - vWorldPos);
    vec3 albedo  = texture(uTexture, vTexCoord * uTileData).rgb;

    if (!uDisableLighting) {
        vec3 result = vec3(0.0);
        
        for (int i = 0; i < uNumPointLights; ++i)
            result += CalcPointLight(pointLights[i], normal, vWorldPos, viewDir);

        for (int i = 0; i < uNumSpotLights; ++i)
            result += CalcSpotLight(spotLights[i], normal, vWorldPos, viewDir);

        FragColor = vec4(result * albedo, 1.0);
    }
    else {
        FragColor = vec4(albedo, 1.0);
    }
}
