
Multi-Level Bilateral Upsampling on the GPU
===========================================

Multi-Level Joint Bilateral Upsampling
--------------------------------------

This function implements a multi-level bilateral filtering technique for joint bilateral upsampling.

This technique upsamples a low-resolution image \(e.g., motion vectors\) using a high-resolution guide image \(itself, color buffer, depth buffer\) while preserving edges. It combines information from the low-resolution image and a downsampled version of the high-resolution guide.

.. seealso::

   Riemens, B., Gangwal, O.P., Barenbrug, B., & Berretty, R. (2009). Multistep joint bilateral depth upsampling. Electronic imaging.

   https://www.semanticscholar.org/paper/Multistep-joint-bilateral-depth-upsampling-Riemens-Gangwal/1ddf9ad017faf63b04778c1ddfc2330d64445da8

Why Multi-Level Bilateral Filtering?
------------------------------------

Joint bilateral upsampling is effective for transferring details from a high-resolution guide to a low-resolution image. However, using a single guide level can lead to artifacts, especially around sharp edges. Multi-level bilateral filtering addresses this by incorporating information from a downsampled version of the guide, providing a wider context for the filtering process. This results in smoother upsampling with better edge preservation.

Source Code
-----------

.. code::

   /*
      This is a function used for Joint Bilateral Upsampling implemented in HLSL. Inspired by Riemens et al. (2009).

      ---

      Riemens, B., Gangwal, O.P., Barenbrug, B., & Berretty, R. (2009). Multistep joint bilateral depth upsampling. Electronic imaging.

      https://www.semanticscholar.org/paper/Multistep-joint-bilateral-depth-upsampling-Riemens-Gangwal/1ddf9ad017faf63b04778c1ddfc2330d64445da8
   */

   float4 CBlur_UpsampleMotionVectors(
      sampler Image,      // This should be 1/2 the size as GuideHigh.
      sampler GuideHigh,  // This should be 2/1 the size as Image and GuideLow.
      sampler GuideLow,   // This should be 1/2 the size as GuideHigh (MipLODBias = 1.0).
      float2 Tex
   )
   {
      const float WeightSigma = 4e-4;
      const float WeightDemoninator = 1.0 / (2.0 * WeightSigma * WeightSigma);
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);

      // Store center pixel for reference.
      float4 Reference = tex2D(GuideHigh, Tex);
      float4 BilateralSum = 0.0;
      float4 WeightSum = 0.0;

      [unroll]
      for (int dx = -1; dx <= 1; ++dx)
      {
            [unroll]
            for (int dy = -1; dy <= 1; ++dy)
            {
               // Calculate offset.
               float2 Offset = float2(float(dx), float(dy));
               float2 OffsetTex = Tex + (Offset * PixelSize);

               // Calculate guide and image samples.
               float4 ImageSample = tex2Dlod(Image, float4(OffsetTex, 0.0, 0.0));
               float4 GuideSample = tex2D(GuideLow, OffsetTex);

               // Calculate the difference and normalize it from FP16 range to [-1.0, 1.0).
               // We normalize the difference to avoid precision loss at higher numbers.
               float2 Difference = CMath_Float2_FP16ToNorm(GuideSample.xy - Reference.xy);
               float SpatialWeight = exp(-dot(Difference, Difference) * WeightDemoninator);
               float Weight = SpatialWeight + exp(-10.0);

               BilateralSum += (ImageSample * Weight);
               WeightSum += Weight;
            }
      }

      return BilateralSum / WeightSum;
   }
