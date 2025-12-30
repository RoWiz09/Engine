#version 330 core

#define MAX_LIGHTS 64

// ----------------------------------------------------
// Per-frame uniforms
// ----------------------------------------------------
uniform vec3 uViewPos;
uniform sampler2D uTexture;
uniform vec2 uTileData;

in vec3 vNormal;
in vec3 vWorldPos;
in vec2 vTexCoord;

out vec4 FragColor;

// ----------------------------------------------------
// Point Light (std140 safe)
// ----------------------------------------------------
struct PointLight {
    vec4 position;     // xyz = position, w = intensity

    vec4 ambient;
    vec4 diffuse;
    vec4 specular;
    vec4 color;

    vec4 attenuation;  // x=constant, y=linear, z=quadratic, w=range
};

layout(std140) uniform PointLightBlock {
    PointLight pointLights[MAX_LIGHTS];
};

uniform int uNumPointLights;

// ----------------------------------------------------
// Spot Light (std140 safe)
// ----------------------------------------------------
struct SpotLight {
    vec4 position;     // xyz position
    vec4 direction;    // xyz normalized

    vec4 angles;       // x=cutOff, y=outerCutOff
    vec4 color;

    vec4 ambient;
    vec4 diffuse;
    vec4 specular;

    vec4 attenuation; // x=constant, y=linear, z=quadratic, w=range
};

layout(std140) uniform SpotLightBlock {
    SpotLight spotLights[MAX_LIGHTS];
};

uniform int uNumSpotLights;

// ----------------------------------------------------
// Spot light calculation
// ----------------------------------------------------
vec3 CalcSpotLight(
    SpotLight light,
    vec3 normal,
    vec3 fragPos,
    vec3 viewDir,
    vec3 albedo
) {
    vec3 lightDir = normalize(light.position.xyz - fragPos);
    float distance = length(light.position.xyz - fragPos);

    if (distance > light.attenuation.w)
        return vec3(0.0);

    // ----- Spotlight cone -----
    float theta = dot(-lightDir, normalize(light.direction.xyz));
    float epsilon = max(light.angles.x - light.angles.y, 0.0001);
    float spotFactor = clamp(
        (theta - light.angles.y) / epsilon,
        0.0,
        1.0
    );

    if (spotFactor <= 0.0)
        return vec3(0.0);

    // ----- Diffuse -----
    float diff = max(dot(normal, lightDir), 0.0);

    // ----- Specular (Blinn-Phong) -----
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(normal, halfwayDir), 0.0), 32.0);

    // ----- Attenuation -----
    float attenuation = 1.0 / (
        light.attenuation.x +
        light.attenuation.y * distance +
        light.attenuation.z * distance * distance
    );

    // ----- Lighting -----
    vec3 ambient  = light.ambient.rgb * albedo;
    vec3 diffuse  = light.diffuse.rgb * diff * albedo * light.color.rgb;
    vec3 specular = light.specular.rgb * spec * light.color.rgb;

    vec3 result =
        ambient +
        (diffuse + specular) * light.position.w;

    return result * attenuation * spotFactor;
}

// ----------------------------------------------------
// Main
// ----------------------------------------------------
void main()
{
    vec3 normal  = normalize(vNormal);
    vec3 viewDir = normalize(uViewPos - vWorldPos);
    vec3 albedo  = texture(uTexture, vTexCoord * uTileData).rgb;

    vec3 result = vec3(0.0);

    // -------- Point Lights --------
    int pointCount = min(uNumPointLights, MAX_LIGHTS);
    for (int i = 0; i < pointCount; ++i)
    {
        PointLight light = pointLights[i];

        vec3 lightDir = normalize(light.position.xyz - vWorldPos);
        float distance = length(light.position.xyz - vWorldPos);

        if (distance > light.attenuation.w)
            continue;

        float diff = max(dot(normal, lightDir), 0.0);

        vec3 halfwayDir = normalize(lightDir + viewDir);
        float spec = pow(max(dot(normal, halfwayDir), 0.0), 32.0);

        float attenuation = 1.0 / (
            light.attenuation.x +
            light.attenuation.y * distance +
            light.attenuation.z * distance * distance
        );

        float rangeFade = 1.0 - clamp(distance / light.attenuation.w, 0.0, 1.0);
        attenuation *= rangeFade * rangeFade;

        vec3 ambient  = light.ambient.rgb * albedo;
        vec3 diffuse  = diff * light.diffuse.rgb * albedo * light.color.rgb;
        vec3 specular = spec * light.specular.rgb * light.color.rgb;

        result +=
            (ambient + (diffuse + specular) * light.position.w)
            * attenuation;
    }

    // -------- Spot Lights --------
    int spotCount = min(uNumSpotLights, MAX_LIGHTS);
    for (int i = 0; i < spotCount; ++i)
    {
        result += CalcSpotLight(
            spotLights[i],
            normal,
            vWorldPos,
            viewDir,
            albedo
        );
    }

    FragColor = vec4(result, 1.0);
}
