
ReShadeFX for Beginners
=======================

Straight to the point:

* **Vertex Shader:** Code that operates on each vertex.
* **Pixel Shader:** Code that operates on each pixel.

What is a Shader?
-----------------

A shader is code that performs mathematical operations.

Think of it like drawing a square:

1.  Define the square's outline.
2.  Connect the outline.
3.  Fill the square with color.

Your First Vertex Shader
------------------------

.. code-block:: none
   :linenos:

   // Vertex shader: Generates a screen-filling triangle.
   // Based on: https://www.reddit.com/r/gamedev/comments/2j17wk/a_slightly_faster_bufferless_vertex_shader_trick/

   void PostProcessVS(
      in uint id : SV_VertexID,           // Vertex ID from CPU.
      out float4 position : SV_Position,  // Vertex position for GPU.
      out float2 texcoord : TEXCOORD      // Texture coordinates for GPU.
   )
   {
      // PART 1: Calculate texture coordinates.
      // Texture coordinates range from 0 to 1.

      texcoord.x = (id == 2) ? 2.0 : 0.0;
      texcoord.y = (id == 1) ? 2.0 : 0.0;

      // PART 2: Calculate clip-space position.
      // Clip-space:
      //   Bottom-left: (-1.0, -1.0)
      //   Top-right: (1.0, 1.0)

      position = float4(texcoord * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);

      // PART 3: GPU clipping and interpolation.
      //   - Fragments outside [-1, 1) are clipped.
      //   - texcoord and position are interpolated.
   }

Your First Pixel Shader
-----------------------

.. code-block:: none
   :linenos:

   // Pixel shader: Colors each pixel of the triangle.

   void PostProcessPS(
      in float2 texcoord : TEXCOORD, // Texture coordinates from GPU.
      out float4 color : SV_Target   // Pixel color for GPU.
   )
   {
      // Use texcoord to set color.
      //   texcoord(1.0, 0.0) -> red
      //   texcoord(0.0, 1.0) -> green
      //   texcoord(1.0, 1.0) -> yellow

      color.r = texcoord.x;
      color.g = texcoord.y;
      color.b = 0.0;
      color.a = 1.0;
   }

Your First Technique
--------------------

.. code-block:: none
   :linenos:

   technique ExampleShader
   {
      pass
      {
         VertexShader = PostProcessVS;
         PixelShader = PostProcessPS;
      }
   }
