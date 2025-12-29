#version 330 core

#define MAX_LIGHTS 64

uniform vec3 uViewPos;
uniform sampler2D uTexture;
uniform vec2 uTileData;

in vec3 vNormal;
in vec3 vWorldPos;
in vec2 vTexCoord;

out vec4 FragColor;

// -------------------- Point Light --------------------
struct PointLight {
    vec3 position;

    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    vec3 color;

    float constant;
    float linear;
    float quadratic;

    float intensity;
    float range;
};

uniform PointLight uPointLights[MAX_LIGHTS];
uniform int uNumPointLights;

// -------------------- Spot Light --------------------
struct SpotLight {
    vec3 position;      // world-space
    vec3 direction;     // normalized (points outward)

    float cutOff;       // cos(inner angle)
    float outerCutOff;  // cos(outer angle)

    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    vec3 color;

    float constant;
    float linear;
    float quadratic;

    float intensity;
    float range;
};

uniform SpotLight uSpotLights[MAX_LIGHTS];
uniform int uNumSpotLights;

// ----------------------------------------------------

vec3 CalcSpotLight(
    SpotLight light,
    vec3 normal,
    vec3 fragPos,
    vec3 viewDir,
    vec3 albedo
) {
    // Direction from fragment → light
    vec3 lightDir = normalize(light.position - fragPos);

    // Distance check (hard range cutoff)
    float distance = length(light.position - fragPos);
    if (distance > light.range)
        return vec3(0.0);

    // ----- Spotlight cone -----
    float theta = dot(-lightDir, normalize(light.direction));
    float epsilon = max(light.cutOff - light.outerCutOff, 0.0001);
    float spotFactor = clamp((theta - light.outerCutOff) / epsilon, 0.0, 1.0);

    if (spotFactor <= 0.0)
        return vec3(0.0);

    // ----- Diffuse -----
    float diff = max(dot(normal, lightDir), 0.0);

    // ----- Specular (Blinn-Phong) -----
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(normal, halfwayDir), 0.0), 32.0);

    // ----- Attenuation (physical) -----
    float attenuation = 1.0 / (
        light.constant +
        light.linear * distance +
        light.quadratic * distance * distance
    );

    // ----- Lighting terms -----
    vec3 ambient  = light.ambient * albedo;
    vec3 diffuse  = light.diffuse * diff * albedo * light.color;
    vec3 specular = light.specular * spec * light.color;

    vec3 color = ambient + (diffuse + specular) * light.intensity;

    return color * attenuation * spotFactor;
}

void main()
{
    vec3 normal = normalize(vNormal);
    vec3 viewDir = normalize(uViewPos - vWorldPos);
    vec3 albedo = texture(uTexture, vTexCoord * uTileData).rgb;

    vec3 result = vec3(0.0);

    // -------- Point Lights --------
    int pointCount = min(uNumPointLights, MAX_LIGHTS);
    for (int i = 0; i < pointCount; ++i)
    {
        PointLight light = uPointLights[i];

        vec3 lightDir = normalize(light.position - vWorldPos);
        float distance = length(light.position - vWorldPos);
        if (distance > light.range)
            continue;

        float diff = max(dot(normal, lightDir), 0.0);

        vec3 halfwayDir = normalize(lightDir + viewDir);
        float spec = pow(max(dot(normal, halfwayDir), 0.0), 32.0);

        float attenuation = 1.0 / (
            light.constant +
            light.linear * distance +
            light.quadratic * distance * distance
        );

        float rangeFade = 1.0 - clamp(distance / light.range, 0.0, 1.0);
        attenuation *= rangeFade * rangeFade;

        vec3 ambient  = light.ambient * albedo;
        vec3 diffuse  = diff * light.diffuse * albedo * light.color;
        vec3 specular = spec * light.specular * light.color;

        result += (ambient + (diffuse + specular) * light.intensity) * attenuation;
    }

    // -------- Spot Lights --------
    int spotCount = min(uNumSpotLights, MAX_LIGHTS - pointCount);
    for (int i = 0; i < spotCount; ++i)
    {
        result += CalcSpotLight(
            uSpotLights[i],
            normal,
            vWorldPos,
            viewDir,
            albedo
        );
    }

    FragColor = vec4(result, 1.0);
}
