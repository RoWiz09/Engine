#version 330 core

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;
uniform mat3 uNormalMatrix;

out vec3 vNormal;
out vec3 vWorldPos;
out vec2 vTexCoord;

void main()
{
    // World-space vertex position
    vWorldPos = vec3(uModel * vec4(aPos, 1.0));

    // World-space normal
    vNormal = normalize(uNormalMatrix * aNormal);

    gl_Position = uProjection * uView * vec4(vWorldPos, 1.0);
    vTexCoord = aTexCoord;
}

