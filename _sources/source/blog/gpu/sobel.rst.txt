
Bilinear Sobel Filtering on The GPU
===================================

The Sobel filter traditionally requires sampling 8 pixels surrounding the center pixel. Leveraging the filter's linearity, we can reduce this to 4 texture fetches by sampling between pixels.

.. code-block:: none
   :caption: Source Code

   struct Sobel
   {
      float4 Ix;
      float4 Iy;
   };

   Sobel GetSobel(sampler SampleImage, float2 Tex, float2 PixelSize)
   {
      Sobel Output;
      float4 A = tex2D(SampleImage, Tex + (float2(-0.5, 0.5) * PixelSize));
      float4 B = tex2D(SampleImage, Tex + (float2(0.5, 0.5) * PixelSize));
      float4 C = tex2D(SampleImage, Tex + (float2(-0.5, -0.5) * PixelSize));
      float4 D = tex2D(SampleImage, Tex + (float2(0.5, -0.5) * PixelSize));
      Output.Ix = (B + D) - (A + C);
      Output.Iy = (A + B) - (C + D);
      return Output;
   }
