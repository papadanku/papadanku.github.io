
Bilinear Sobel Filtering in HLSL
================================

The Sobel filter requires you to sample 8 pixels around the center pixel. The filter is linear, so you can sample 8 pixels in 4 texture fetches by sampling in-between pixels.

Source Code
-----------

.. code-block:: c

   struct Sobel
   {
      float4 Ix;
      float4 Iy;
   };

   Sobel GetSobel(sampler SampleImage, float2 Tex, float2 PixelSize)
   {
      Sobel Output;
      float4 A = tex2D(SampleImage, Tex + (float2(-0.5, +0.5) * PixelSize));
      float4 B = tex2D(SampleImage, Tex + (float2(+0.5, +0.5) * PixelSize));
      float4 C = tex2D(SampleImage, Tex + (float2(-0.5, -0.5) * PixelSize));
      float4 D = tex2D(SampleImage, Tex + (float2(+0.5, -0.5) * PixelSize));
      Output.Ix = (B + D) - (A + C);
      Output.Iy = (A + B) - (C + D);
      return Output;
   }
