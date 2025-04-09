
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

   float4 JointBilateralUpsample(
      sampler Image, // This should be 1/2 the size as GuideHigh
      sampler GuideLow, // This should be 1/2 the size as GuideHigh
      sampler GuideHigh, // This should be 2/1 the size as Image and GuideLow
      float2 Tex
   )
   {
      // Initialize variables
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float4 GuideHighSample = tex2D(GuideHigh, Tex);
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

            // Sample image and guide
            float4 ImageSample = tex2Dlod(Image, float4(OffsetTex, 0.0, 0.0));
            float4 GuideLowSample = tex2D(GuideLow, OffsetTex);

            // Calculate weight
            float3 Delta = GuideLowSample.xyz - GuideHighSample.xyz;
            float Weight = 1.0 / dot(Delta, Delta);
            Weight = (Weight > 0.0) ? Weight + exp(-10.0) : 1.0;

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
   :caption: Self-Guided Bilateral Upsampling

   float4 BilateralUpsampleXY(
      sampler Image, // This should be 1/2 the size as GuideHigh
      sampler Guide, // This should be 2/1 the size as Image and GuideLow
      float2 Tex
   )
   {
      // Initialize variables
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float4 GuideHighSample = tex2D(Guide, Tex);
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

            // Calculate weight
            float2 Delta = CMath_Float2_FP16ToNorm(ImageSample.xy - GuideHighSample.xy);
            float Weight = 1.0 / dot(Delta, Delta);
            Weight = (Weight > 0.0) ? Weight + exp(-10.0) : 1.0;

            BilateralSum += (ImageSample * Weight);
            WeightSum += Weight;
         }
      }

      return BilateralSum / WeightSum;
   }
