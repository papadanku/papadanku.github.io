
Multi-Level Bilateral Upsampling on the GPU
===========================================

This function implements a multi-level bilateral filtering technique for joint bilateral upsampling.

This technique upsamples a low-resolution image \(e.g., motion vectors\) using a high-resolution guide image \(the image itself, color buffer, depth buffer\) while preserving edges. It combines information from the low-resolution image and a downsampled version of the high-resolution guide.

.. seealso::

   Riemens, B., Gangwal, O.P., Barenbrug, B., & Berretty, R. \(2009\). Multistep joint bilateral depth upsampling. Electronic imaging.

   https://www.semanticscholar.org/paper/Multistep-joint-bilateral-depth-upsampling-Riemens-Gangwal/1ddf9ad017faf63b04778c1ddfc2330d64445da8

Multi-Level Bilateral Filtering
-------------------------------

Joint bilateral upsampling effectively transfers details from a high-resolution guide to a low-resolution image. However, using a single guide level can lead to artifacts, especially around sharp edges. Multi-level bilateral filtering addresses this by incorporating information from a downsampled version of the guide, providing a broader context for the filtering process. This results in smoother upsampling with better edge preservation.

.. code-block:: none
   :caption: Joint Bilateral Upsampling

   /*
      This is a function used for Joint Bilateral Upsampling implemented in HLSL. Inspired by Riemens et al. (2009).

      ---

      Riemens, B., Gangwal, O.P., Barenbrug, B., & Berretty, R. (2009). Multistep joint bilateral depth upsampling. Electronic imaging.

      https://www.semanticscholar.org/paper/Multistep-joint-bilateral-depth-upsampling-Riemens-Gangwal/1ddf9ad017faf63b04778c1ddfc2330d64445da8
   */

   float4 UpsampleMotionVectors(
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

               // Calculate weight
               float2 Difference = GuideSample.xy - Reference.xy;
               float SpatialWeight = exp(-dot(Difference, Difference) * WeightDemoninator);
               float Weight = SpatialWeight + exp(-10.0);

               BilateralSum += (ImageSample * Weight);
               WeightSum += Weight;
            }
      }

      return BilateralSum / WeightSum;
   }

Self-Guided Optimization
------------------------

In the original multi-level bilateral filtering approach, the spatial weight is calculated using the difference between the high-resolution guide and its downsampled version. However, in scenarios where the low-resolution image and the downsampled guide share similar properties \(e.g., when the guide is derived from the image itself\), we can simplify the process by directly using the low-resolution image for calculating the spatial weight.

This modification eliminates the need for an explicit downsampled guide and can improve performance by reducing texture fetches. Using the image as a guide, we maintain the edge-preserving characteristics while optimizing the computation.

.. code-block:: none
   :caption: Joint Bilateral Upsampling (Self-Guided)

   float4 UpsampleMotionVectors(
      sampler Image, // This should be 1/2 the size as Guide
      sampler Guide, // This should be 2/1 the size as Image
      float2 Tex
   )
   {
      const float WeightSigma = 4e-4;
      const float WeightDemoninator = 1.0 / (2.0 * WeightSigma * WeightSigma);
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);

      // Store center pixel for reference
      float4 Reference = tex2D(Guide, Tex);
      float4 BilateralSum = 0.0;
      float4 WeightSum = 0.0;

      [unroll]
      for (int dx = -1; dx <= 1; ++dx)
      {
            [unroll]
            for (int dy = -1; dy <= 1; ++dy)
            {
               // Calculate offset
               float2 Offset = float2(float(dx), float(dy));
               float2 OffsetTex = Tex + (Offset * PixelSize);

               // Calculate the difference and normalize it from FP16 range to [-1.0, 1.0) range
               // We normalize the difference to avoid precision loss at the higher numbers
               float4 ImageSample = tex2Dlod(Image, float4(OffsetTex, 0.0, 0.0));
               float2 Difference = ImageSample.xy - Reference.xy;
               float SpatialWeight = exp(-dot(Difference, Difference) * WeightDemoninator);
               float Weight = SpatialWeight + exp(-10.0);

               BilateralSum += (ImageSample * Weight);
               WeightSum += Weight;
            }
      }

      return BilateralSum / WeightSum;
   }
