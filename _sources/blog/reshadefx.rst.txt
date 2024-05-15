
ReShadeFX for Beginners
=======================

No bullshit, just move along.

What is a Shader?
-----------------

A shader is code that does math.

A shader is like a drawing a square. Here is how you draw a red square:

#. You draw a dotted outline of the square.
#. You connect the dotted outline of the square.
#. You color red inside the square.

Your First Vertex Shader
------------------------

::
    :number-lines:

    // Vertex shader generating a triangle covering the entire screen
    // See also https://www.reddit.com/r/gamedev/comments/2j17wk/a_slightly_faster_bufferless_vertex_shader_trick/
    void PostProcessVS(in uint id : SV_VertexID, out float4 position : SV_Position, out float2 texcoord : TEXCOORD)
    {
        texcoord.x = (id == 2) ? 2.0 : 0.0;
        texcoord.y = (id == 1) ? 2.0 : 0.0;
        position = float4(texcoord * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
    }

Your First Pixel Shader
-----------------------



Your First Technique
--------------------


Recap
-----

.. glossary::

    :Vertex Shader: Code that does math on every vertex
    :Pixel Shader: Code that does math on
