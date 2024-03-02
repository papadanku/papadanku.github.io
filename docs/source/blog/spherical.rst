
Spherical Chromaticity in HLSL
==============================

This post introduces a color space that computes chromaticity with angles.

Precision Loss in RG Chromaticity
---------------------------------

Pecision is a major drawback to RG chromaticity. In RG chromaticity, all possible values map into a right-triangle, eliminating half of the precision in integer buffers.

We can encode data that fits in the entire ``RG8`` range by calculating the angles between the channels.

Source Code
-----------

.. code-block:: c

   float2 GetSphericalRG(float3 Color)
   {
      const float IHalfPi = 1.0 / acos(0.0);
      const float2 White = acos(rsqrt(float2(2.0, 3.0)));

      float2 DotC = 0.0;
      DotC.x = dot(Color.xy, Color.xy);
      DotC.y = dot(Color.xyz, Color.xyz);
      float2 P = (DotC == 0.0) ? White : acos(abs(Color.xz * rsqrt(DotC)));
      return saturate(P * IHalfPi);
   }
