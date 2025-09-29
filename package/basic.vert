#version 330 core

layout(location = 0) in vec3 aPos;   // vertex position

uniform mat4 uModel;      // model matrix
uniform mat4 uView;       // view matrix
uniform mat4 uProjection; // projection matrix

void main()
{
    gl_Position = uProjection * uView * uModel * vec4(aPos, 1.0);
}
