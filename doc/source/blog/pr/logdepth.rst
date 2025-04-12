
Logarithmic Depth Buffering
===========================

The `Project Reality Team <https://www.realitymod.com/>`_ implemented logarithmic depth buffering in their 1.7.3 update. This document outlines a simplified implementation of logarithmic depth buffering in HLSL, based on `Outerra's optimized GLSL approach from 2013 <https://outerra.blogspot.com/2013/07/logarithmic-depth-buffer-optimizations.html>`_.

.. code-block:: none
   :caption: Logarithmic Depth Buffering Pixel Shader

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

   // Converts linear depth to logarithmic depth in the pixel shader.
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

      // Apply world-view-projection transformation.
      Output.HPos = mul(Input.Pos, _WorldViewProj);

      // Output depth (w-component of homogeneous position + 1).
      Output.Depth = Output.HPos.w + 1.0;

      return Output;
   }

   PS2FB PS_LogDepth(VS2PS Input)
   {
      PS2FB Output;

      // Output a color value (required).
      Output.Color = 0.0;

      // Output logarithmic depth for per-fragment depth testing.
      Output.Depth = ApplyLogarithmicDepth(Input.Depth);

      return Output;
   }

Correcting Outerra's Logarithmic Depth Buffering
------------------------------------------------

Outerra provides a vertex shader implementation of logarithmic depth buffering in GLSL (`outerra.blogspot.com <https://outerra.blogspot.com/2013/07/logarithmic-depth-buffer-optimizations.html>`_). However, their implementation omits a crucial step. This document presents a corrected version of Outerra's logarithmic depth buffering in HLSL.

Outerra's implementation lacks a final multiplication by the homogeneous coordinate 'W'. This multiplication is essential because the GPU automatically divides the vertex position `HPos` by `W` during the perspective divide.

.. code-block:: none

   // Output.HPos is the computed vertex position in homogeneous space.
   const float FarPlane = 10000.0;
   const float FCoef = 1.0 / log2(FarPlane + 1.0);
   Output.HPos.z = saturate(log2(max(1e-6, Output.HPos.w)) * FCoef);
   Output.HPos.z *= Output.HPos.w;
