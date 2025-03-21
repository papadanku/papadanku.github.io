
RasterGrid's Gaussian Blur on The GPU
=====================================

Gaussian blurs sample many pixels. `RasterGrid optimized Gaussian blur by sampling in-between pixels <https://www.rastergrid.com/blog/2010/09/efficient-Gaussian-blur-with-linear-sampling/>`_. RasterGrid's article did not include shader code for varied Gaussian blur radii. This post solves that.

.. code-block:: none
   :caption: Source Code

   float GetGaussianWeight(float SampleIndex, float Sigma)
   {
      const float Pi = acos(-1.0);
      float Output = rsqrt(2.0 * Pi * (Sigma * Sigma));
      return Output * exp(-(SampleIndex * SampleIndex) / (2.0 * Sigma * Sigma));
   }

   float GetGaussianOffset(float SampleIndex, float Sigma, out float LinearWeight)
   {
      float Offset1 = SampleIndex;
      float Offset2 = SampleIndex + 1.0;
      float Weight1 = GetGaussianWeight(Offset1, Sigma);
      float Weight2 = GetGaussianWeight(Offset2, Sigma);
      LinearWeight = Weight1 + Weight2;
      return ((Offset1 * Weight1) + (Offset2 * Weight2)) / LinearWeight;
   }

   float4 GetGaussianBlur(float2 Tex, float LOD, float2 PixelSize, float Sigma)
   {
      // Sample and weight center first to get even number sides
      float TotalWeight = GetGaussianWeight(0.0, Sigma);
      float4 OutputColor = tex2Dlod(SampleColorTex, float4(Tex, 0.0, LOD)) * TotalWeight;

      for(float i = 1.0; i < Sigma * 3.0; i += 2.0)
      {
         float LinearWeight = 0.0;
         float LinearOffset = GetGaussianOffset(i, Sigma, LinearWeight);
         OutputColor += tex2Dlod(SampleColorTex, float4(Tex - (LinearOffset * PixelSize), 0.0, LOD)) * LinearWeight;
         OutputColor += tex2Dlod(SampleColorTex, float4(Tex + (LinearOffset * PixelSize), 0.0, LOD)) * LinearWeight;
         TotalWeight += LinearWeight * 2.0;
      }

      // Normalize intensity to prevent altered output
      return OutputColor / TotalWeight;
   }
