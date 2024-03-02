
Logarithmic Depth Buffering in HLSL
===================================

`The Project Reality Team <https://www.realitymod.com/>`_ implemented logarithmic depth buffering for the 1.7.3 update. This post covers our implementation of simple logarithmic depth buffering in HLSL.

`Outerra has an optimized 2013 implementation of logarithmic depth in GLSL <https://outerra.blogspot.com/2013/07/logarithmic-depth-buffer-optimizations.html>`_. This is our simplified version of Outerra’s logarithmic depth in HLSL.

Source Code
-----------

.. code-block:: c

   float4x4 _WorldViewProj : WorldViewProj;

   struct APP2VS
   {
      float4 Pos : POSITION0;
   };

   struct VS2PS
   {
      float4 HPos : POSITION;
      float Depth : TEXCOORD0;
   };

   struct PS2FB
   {
      float4 Color : COLOR;
      float Depth : DEPTH;
   };

   // Converts linear depth to logarithmic depth in the pixel shader
   // Source: https://outerra.blogspot.com/2013/07/logarithmic-depth-buffer-optimizations.html
   float ApplyLogarithmicDepth(float Depth)
   {
      const float FarPlane = 10000.0;
      const float FCoef = 1.0 / log2(FarPlane + 1.0);
      return log2(Depth) * FCoef;
   }

   VS2PS VS_LogDepth(APP2VS Input)
   {
      VS2PS Output = (VS2PS)0;

      // Usually a transformation happens here
      Output.HPos = mul(float4(Input.Pos.xyz, 1.0), _WorldViewProj);

      // Output depth
      Output.Depth = Output.HPos.w + 1.0;

      return Output;
   }

   PS2FB PS_LogDepth(VS2PS Input)
   {
      PS2FB Output;

      // You need to output something to the color buffer
      Output.Color = 0.0;

      // You must output to the pixel shader’s DEPTH semantic so the GPU can do per-fragment depth testing.
      Output.Depth = ApplyLogarithmicDepth(Input.Depth);

      return Output;
   };
