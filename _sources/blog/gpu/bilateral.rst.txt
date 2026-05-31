
Multi-Level Bilateral Upsampling on the GPU
===========================================

This function implements a multi-level bilateral filtering technique for joint bilateral upsampling.

This technique upsamples a low-resolution image \(e.g., motion vectors\) using a high-resolution guide image \(the image itself, color buffer, depth buffer\) while preserving edges. It combines information from the low-resolution image and a downsampled version of the high-resolution guide.

.. seealso::

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

Multi-Level Bilateral Filtering
-------------------------------

Joint bilateral upsampling effectively transfers details from a high-resolution guide to a low-resolution image. However, using a single guide level can lead to artifacts, especially around sharp edges. Multi-level bilateral filtering addresses this by incorporating information from a downsampled version of the guide, providing a broader context for the filtering process. This results in smoother upsampling with better edge preservation.

.. code-block:: hlsl
   :caption: Joint Bilateral Upsampling

   /*
      Joint Bilateral Upsampling implemented in HLSL. Inspired by Kopf et al. (2007) and Riemens et al. (2009).

      ---

      Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

      Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640
   */

   // Initialize variables to compute
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
      float BilateralWeightSum = 0.0;

      [unroll]
      for (int x = -1; x <= 1; x++)
      {
         [unroll]
         for (int y = -1; y <= 1; y++)
         {
            // Calculate offset
            float2 Offset = float2(x, y);
            float2 OffsetTex = Tex + (Offset * PixelSize);

            // Sample image and guide
            float4 ImageSample = tex2D(Image, OffsetTex);
            float4 GuideLowSample = tex2D(GuideLow, OffsetTex);

            // Calculate weight
            float4 D = GuideHighSample - GuideLowSample;
            float2 DotDD = float2(dot(D.xy, D.xy), dot(D.zw, D.zw));
            float2 Weights = smoothstep(0.0, 1.0, rsqrt(DotDD + 1.0));
            float Weight = rsqrt(dot(Offset, Offset) + 1.0);
            Weight *= Weights[0] * Weights[1];

            // Accumulate bilateral
            BilateralSum += (ImageSample * Weight);
            BilateralWeightSum += Weight;
         }
      }

      BilateralSum = BilateralSum / BilateralWeightSum;

      return BilateralSum;
   }

Adaptive, Multi-Level, Self-Guided Bilateral Filtering
------------------------------------------------------

In the original multi-level bilateral filtering approach, the spatial weight is calculated using the difference between the high-resolution guide and its downsampled version. However, in scenarios where the low-resolution image and the downsampled guide share similar properties \(e.g., when the guide is derived from the image itself\), we can simplify the process by directly using the low-resolution image for calculating the spatial weight.

This modification eliminates the need for an explicit downsampled guide and can improve performance by reducing texture fetches. Using the image as a guide, we maintain the edge-preserving characteristics while optimizing the computation.

.. code-block:: hlsl
   :caption: Self-Guided Bilateral Upsampling

   /*
      This is an optimized, self-guided version for Joint Bilateral Upsampling implemented in HLSL. Inspired by Kopf et al. (2007) and Riemens et al. (2009).

      ---

      Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

      Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640
   */

   float2 SelfBilateralUpsampleXY(
      sampler Image, // This should be 1/2 the size as GuideHigh
      sampler Guide, // This should be 2/1 the size as Image and GuideLow
      float2 Tex
   )
   {
      // Constants: Mean
      const int ArrayCount = 9;
      const float ArrayN = 1.0 / float(ArrayCount);
      const float VarianceN = 1.0 / (float(ArrayCount) - 1.0);

      // Constants: Sensitivity and regularize variance to prevent division by zero
      const float BaseSigmaR = 0.0;
      const float SensitivityMultiplier = 1.0;

      // Precompute
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float2 GuideCenter = tex2D(Guide, Tex).xy;

      int ImageIndex = 0;
      float2 ImageArray[ArrayCount];
      float2 OffsetArray[ArrayCount];

      float2 Mean = 0.0;
      float Variance = 0.0;

      // Gather samples and calculate mean
      [unroll]
      for (int x = -1; x <= 1; x++)
      {
         [unroll]
         for (int y = -1; y <= 1; y++)
         {
            float2 Offset = float2(x, y);
            if ((x == 0) && (y == 0))
            {
               ImageArray[ImageIndex] = tex2D(Image, Tex).xy;
               OffsetArray[ImageIndex] = Offset;
            }
            else
            {
               ImageArray[ImageIndex] = tex2D(Image, Tex + (DiskOffset * PixelSize)).xy;
               OffsetArray[ImageIndex] = DiskOffset;
            }

            Mean += (ImageArray[ImageIndex] * ArrayN);
            ImageIndex += 1;
         }
      }

      [unroll]
      for (int j = 0; j < ArrayCount; j++)
      {
         // Total variance handles both X and Y components combined
         float2 Diff = ImageArray[j] - Mean;
         Variance += (dot(Diff, Diff) * VarianceN);
      }

      // The sigma scales based on local variance
      float Sigma = sqrt(Variance + 1e-7);
      float SigmaSq = 1.0 / (2.0 * (Sigma * Sigma));

      float2 BilateralSum = 0.0;
      float BilateralWeightSum = 0.0;

      // Evaluate weights using the adaptive range denominator
      [unroll]
      for (int i = 0; i < ArrayCount; i++)
      {
         float Weight = 1.0;

         // Range weight
         float2 Delta = ImageArray[i] - GuideCenter;
         float DistSqRange = dot(Delta, Delta);
         float WeightRange = 1.0 / (DistSqRange + SigmaSq);
         Weight *= WeightRange;

         // Spatial weight
         float DistSqSpatial = dot(OffsetArray[i], OffsetArray[i]);
         float WeightSpatial = rsqrt(DistSqSpatial + 1.0);
         Weight *= WeightSpatial;

         BilateralSum += (ImageArray[i] * Weight);
         BilateralWeightSum += Weight;
      }

      return (BilateralWeightSum > 0.0) ? (BilateralSum / BilateralWeightSum) : Mean;
   }
