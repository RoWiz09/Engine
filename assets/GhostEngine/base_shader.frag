#version 330 core

#define MAX_LIGHTS 64

uniform vec3 uViewPos;
uniform sampler2D uTexture;
uniform vec2 uTileData;

in vec3 vNormal;
in vec3 vWorldPos;
in vec2 vTexCoord;

out vec4 FragColor;

// Point Light
struct PointLight {
    vec4 position;
    vec4 ambient;
    vec4 diffuse;
    vec4 specular;
    vec4 color;
    vec4 attenuation;
};

layout(std140) uniform PointLightBlock {
    PointLight pointLights[MAX_LIGHTS];
};

uniform int uNumPointLights;

// Spot Light
struct SpotLight {
    vec4 position;
    vec4 direction;
    vec4 angles;
    vec4 color; 
    vec4 ambient;
    vec4 diffuse;
    vec4 specular;
    vec4 attenuation;
};

layout(std140) uniform SpotLightBlock {
    SpotLight spotLights[MAX_LIGHTS];
};

uniform int uNumSpotLights;

// Point Light Calculation
vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
{
    vec3 L = normalize(light.position.xyz - fragPos);
    float distance = length(light.position.xyz - fragPos);

    if(distance > light.attenuation.w)
        return vec3(0.0);

    float diff = max(dot(normal, L), 0.0);
    vec3 H = normalize(L + viewDir);
    float spec = pow(max(dot(normal, H), 0.0), 32.0);

    float atten = 1.0 / (light.attenuation.x + light.attenuation.y*distance + light.attenuation.z*distance*distance);
    float rangeFade = 1.0 - clamp(distance / light.attenuation.w, 0.0, 1.0);
    atten *= rangeFade * rangeFade;

    vec3 ambient  = light.ambient.rgb * light.color.rgb;
    vec3 diffuse  = light.diffuse.rgb  * diff * light.color.rgb;
    vec3 specular = light.specular.rgb * spec * light.color.rgb;

    return (ambient + (diffuse + specular)) * atten * light.position.w;
}

// Spot Light Calculation
vec3 CalcSpotLight(SpotLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
{
    vec3 L = normalize(light.position.xyz - fragPos);
    float distance = length(light.position.xyz - fragPos);

    if(distance > light.attenuation.w)
        return vec3(0.0);

    float theta = dot(L, normalize(light.direction.xyz));
    float epsilon = light.angles.x - light.angles.y;
    float intensity = clamp((theta - light.angles.y) / max(epsilon, 0.001), 0.0, 1.0);

    if(intensity <= 0.0)
        return vec3(0.0);

    float diff = max(dot(normal, L), 0.0);
    vec3 H = normalize(L + viewDir);
    float spec = pow(max(dot(normal, H), 0.0), 32.0);

    float atten = 1.0 / (light.attenuation.x + light.attenuation.y*distance + light.attenuation.z*distance*distance);
    float rangeFade = 1.0 - clamp(distance / light.attenuation.w, 0.0, 1.0);
    atten *= rangeFade * rangeFade;

    vec3 ambient  = light.ambient.rgb * light.color.rgb;
    vec3 diffuse  = light.diffuse.rgb  * diff * light.color.rgb;
    vec3 specular = light.specular.rgb * spec * light.color.rgb;

    vec3 result = ambient + diffuse + specular;

    return result * atten * light.position.w;
}

// Main
void main()
{
    vec3 normal  = normalize(vNormal);
    vec3 viewDir = normalize(uViewPos - vWorldPos);
    vec3 albedo  = texture(uTexture, vTexCoord * uTileData).rgb;

    vec3 result = vec3(0.0);

    int pointCount = min(uNumPointLights, MAX_LIGHTS);
    for(int i=0; i<pointCount; ++i)
        result += CalcPointLight(pointLights[i], normal, vWorldPos, viewDir);

    int spotCount = min(uNumSpotLights, MAX_LIGHTS);
    for(int i=0; i<spotCount; ++i)
        result += CalcSpotLight(spotLights[i], normal, vWorldPos, viewDir);

    FragColor = vec4(result * albedo, 1.0);

    // if (!gl_FrontFacing)
    //     FragColor = vec4(1, 0, 0, 1);
    // else
    //     FragColor = vec4(0, 1, 0, 1);
}
