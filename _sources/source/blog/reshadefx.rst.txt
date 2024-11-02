
ReShadeFX for Beginners
=======================

No bullshit, just move along.

Recap
    :Vertex Shader: Code that does math on every vertex
    :Pixel Shader: Code that does math on every pixel

What is a Shader?
-----------------

A shader is code that does math.

A shader is like a drawing a square. Here is how you draw a red square:

#. You draw a dotted outline of the square.
#. You connect the dotted outline of the square.
#. You color red inside the square.

Your First Vertex Shader
------------------------

.. code::
    :number-lines:

    // Vertex shader generating a triangle covering the entire screen.
    // See also https://www.reddit.com/r/gamedev/comments/2j17wk/a_slightly_faster_bufferless_vertex_shader_trick/

    // Make a function that calculate on each vertex.
    // PostProcessVS() outputs a triangle that is twice the screen's size.
    void PostProcessVS
    (
        in uint id : SV_VertexID, // Get "id" from CPU memory named "SV_VertexID"
        out float4 position : SV_Position, // Send "position" to GPU memory named "SV_Position"
        out float2 texcoord : TEXCOORD // Send "texcoord" to GPU memory named "TEXCOORD"
    )
    {
        /*
            PART 1
            ---
            Use the vertex's ID to calculate its texture coordinates.
            NOTE: Texture coordinates are 0-1
            ---
            ID 0 -> texcoord (0.0, 0.0)
            ID 1 -> texcoord (0.0, 2.0)
            ID 2 -> texcoord (2.0, 0.0)
        */

        // If the vertex's ID is 2, set the its texcoord's X position to 2.
        // If the vertex's ID is not 2, set its texcoord's X position to 0.
        texcoord.x = (id == 2) ? 2.0 : 0.0;

        // If the vertex's ID is 1, set the its texcoord's Y position to 2.
        // If the vertex's ID is not 1, set its texcoord's Y position to 0.
        texcoord.y = (id == 1) ? 2.0 : 0.0;

        /*
            PART 2
            ---
            We stretch the triangle to be twice the size of the screen.
            To do this, use the vertex's texture coordinates to calculate it's position in clip-space.

            In clip-space, the values represent:
                Bottom-left of screen: (-1.0, -1.0)
                Bottom-right of screen: (1.0, -1.0)
                Top-left of screen: (-1.0, 1.0)
                Top-right of screen: (1.0, 1.0)
            ---
            texcoord (0.0, 0.0) -> position (-1.0, 1.0)
            texcoord (0.0, 2.0) -> position (-1.0, 3.0)
            texcoord (2.0, 0.0) -> position (3.0, 1.0)
        */

        position = float4(texcoord * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);

        /*
            PART 3
            ---
            1. The GPU will "clip" fragments that have a position beyond -1 or 1.
            2. The GPU will interpolate the "texcoord" and "position" data between vertices
        */
    }

Your First Pixel Shader
-----------------------

.. code::
    :number-lines:

    // Make a function that calculate on each pixel.
    // PostProcessPS() outputs a color on each of the triangle's pixel.
    void PostProcessPS
    (
        in float2 texcoord : TEXCOORD, // Get "texcoord" from GPU memory named "TEXCOORD"
        out float4 color : SV_Target // Send "color" to GPU memory named "SV_Target"
    )
    {
        /*
            Use the texcoord's XY value to set the triangle's red and green value.
                texcoord(1.0, 0.0) -> color(1.0, 0.0, 0.0, 1.0) -> all red
                texcoord(0.0, 1.0) -> color(1.0, 0.0, 0.0, 1.0) -> all green
                texcoord(1.0, 1.0) -> color(1.0, 1.0, 0.0, 1.0) -> mix of red and green
        */
        color.r = texcoord.x;
        color.g = texcoord.y;
        color.b = 0.0;
        color.a = 1.0;
    }

Your First Technique
--------------------

.. code::
    :number-lines:

    technique ExampleShader
    {
        pass
        {
            VertexShader = PostProcessVS;
            PixelShader = PostProcessPS;
        }
    }
