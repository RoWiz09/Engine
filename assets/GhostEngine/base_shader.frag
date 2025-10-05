#version 330 core

in vec3 vWorldPos;
in vec3 vNormal;
in vec2 vTexCoord;

out vec4 FragColor;

// ---------------- material ----------------
uniform vec3 uMaterialSpecular;
uniform float uMaterialShininess;

uniform sampler2D uDiffuseMap;  // always bound

// ---------------- camera ----------------
uniform vec3 uCameraPos;

// ---------------- directional light ----------------
struct DirectionalLight {
    vec3 direction;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};
uniform DirectionalLight uDirLight;

// ---------------- point lights ----------------
struct PointLight {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float constant;
    float linear;
    float quadratic;
};

#define MAX_POINT_LIGHTS 16   // set your maximum
uniform int uNumPointLights;
uniform PointLight uPointLights[MAX_POINT_LIGHTS];

// ---------------- functions ----------------
vec3 CalcDirectionalLight(DirectionalLight light, vec3 normal, vec3 viewDir, vec3 albedo) {
    vec3 lightDir = normalize(-light.direction);
    float diff = max(dot(normal, lightDir), 0.0);

    vec3 halfDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(normal, halfDir), 0.0), uMaterialShininess);

    vec3 ambient  = light.ambient  * albedo;
    vec3 diffuse  = light.diffuse  * diff * albedo;
    vec3 specular = light.specular * spec * uMaterialSpecular;
    return ambient + diffuse + specular;
}

vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir, vec3 albedo) {
    vec3 lightDir = normalize(light.position - fragPos);
    float diff = max(dot(normal, lightDir), 0.0);

    vec3 halfDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(normal, halfDir), 0.0), uMaterialShininess);

    float distance    = length(light.position - fragPos);
    float attenuation = 1.0 / (light.constant + light.linear * distance + light.quadratic * (distance * distance));

    vec3 ambient  = light.ambient  * albedo;
    vec3 diffuse  = light.diffuse  * diff * albedo;
    vec3 specular = light.specular * spec * uMaterialSpecular;

    return (ambient + diffuse + specular) * attenuation;
}

void main() {
    // albedo from diffuse texture
    vec3 albedo = texture(uDiffuseMap, vTexCoord).rgb;

    vec3 normal  = normalize(vNormal);
    vec3 viewDir = normalize(uCameraPos - vWorldPos);

    vec3 result = vec3(0.0);

    // directional
    result += CalcDirectionalLight(uDirLight, normal, viewDir, albedo);

    // point lights
    for(int i = 0; i < uNumPointLights; i++) {
        result += CalcPointLight(uPointLights[i], normal, vWorldPos, viewDir, albedo);
    }

    // gamma correction
    const float gamma = 2.2;
    vec3 color = pow(result, vec3(1.0 / gamma));

    FragColor = vec4(color, 1.0);
}
