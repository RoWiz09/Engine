#version 330 core

uniform vec3 uViewPos;       // camera position
uniform sampler2D uTexture;

uniform vec2 uTileData;

in vec3 vNormal;
in vec3 vWorldPos;
in vec2 vTexCoord;

out vec4 FragColor;

const int MAX_LIGHTS = 64;

// ------ Point Light ------
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

// ------ Spot Light ------
struct SpotLight {
    vec3 position;      // world-space
    vec3 direction;     // normalized

    // DON'T FORGET TO COS THIS, IDIOT!
    float cutOff;
    float outerCutOff;

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

uniform int uNumSpotLights;
uniform SpotLight uSpotLights[MAX_LIGHTS];

uniform bool past_stable_max = false;

vec3 CalcSpotLight(SpotLight light, vec3 normal, vec3 fragPos, vec3 viewDir, vec3 albedo)
{
    vec3 lightDir = normalize(light.position - fragPos);

    // ----- Diffuse -----
    float diff = max(dot(normal, lightDir), 0.0);

    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(normal, halfwayDir), 0.0), 32.0);

    float theta = dot(lightDir, normalize(light.direction));
    float epsilon = light.cutOff - light.outerCutOff;
    float spotFactor = clamp((theta + light.outerCutOff) / epsilon, 0.0, 1.0); // Apparently flipping a + to a - absolutely FUCKS rotated lighting. Don't ask me why.

    float d = length(light.position - fragPos);
    float attenuation = 1.0 - clamp(d / light.range, 0.0, 1.0);
    attenuation *= attenuation;  
    
    vec3 ambient  = light.ambient  * albedo;
    vec3 diffuse  = light.diffuse  * diff * albedo * light.intensity * light.color;
    vec3 specular = light.specular * spec * light.intensity * light.color;

    return (ambient + (diffuse + specular) * spotFactor) * attenuation;
}

void main()
{
    vec3 normal = normalize(vNormal);
    vec3 result = vec3(0.0);

    vec3 albedo = texture(uTexture, vTexCoord*uTileData).rgb;
    vec3 viewDir = normalize(uViewPos - vWorldPos);

    int cur_processed_lights = 0;
    for (int i = 0; i < uNumPointLights; i++)
    {
        if (cur_processed_lights > MAX_LIGHTS){
            break;
        }

        PointLight light = uPointLights[i];
        vec3 lightDir = normalize(light.position - vWorldPos);

        vec3 ambient = light.ambient * albedo;

        float diff = max(dot(normal, lightDir), 0.0);
        vec3 diffuse = diff * light.diffuse * albedo * light.intensity * light.color;

        vec3 halfwayDir = normalize(lightDir + viewDir);
        float spec = pow(max(dot(normal, halfwayDir), 0.0), 32.0);
        vec3 specular = spec * light.specular * light.intensity * light.color;

        float distance = length(light.position - vWorldPos);
        float attenuation = 1.0 / (light.constant +
                           light.linear * distance +
                           light.quadratic * distance * distance);

        attenuation *= clamp(1.0 - (distance / light.range), 0.0, 1.0);

        result += (ambient + diffuse + specular) * attenuation;

        cur_processed_lights ++;
    }

    for (int i = 0; i < uNumSpotLights; i++)
    {
        if (cur_processed_lights > MAX_LIGHTS){
            break;
        }

        result += CalcSpotLight(uSpotLights[i], normal, vWorldPos, viewDir, albedo);
        cur_processed_lights ++;
    }

    FragColor = vec4(result, 1.0);
}
