
Multi-Level Bilateral Upsampling on The GPU
===========================================

This function implements a multi-level bilateral filtering technique for joint bilateral upsampling.

This technique upsamples a low-resolution image \(e.g., motion vectors\) using a high-resolution guide image \(the image itself, color buffer, depth buffer\) while preserving edges. It combines information from the low-resolution image and a downsampled version of the high-resolution guide.

.. seealso::

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

Multi-Level Bilateral Filtering
-------------------------------

Joint bilateral upsampling effectively transfers details from a high-resolution guide to a low-resolution image. However, using a single guide level can lead to artifacts, especially around sharp edges. Multi-level bilateral filtering addresses this by incorporating information from a downsampled version of the guide, providing a broader context for the filtering process. This results in smoother upsampling with better edge preservation.

.. code-block:: none
   :caption: Joint Bilateral Upsampling

   /*
      Joint Bilateral Upsampling implemented in HLSL. Inspired by Kopf et al. (2007) and Riemens et al. (2009).

      ---

      Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

      Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640
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
      for (int dx = -1; dx <= 1; dx++)
      {
         [unroll]
         for (int dy = -1; dy <= 1; dy++)
         {
            // Calculate offset
            float2 Offset = float2(float(dx), float(dy));
            float2 OffsetTex = Tex + (Offset * PixelSize);

            // Sample image and guide
            float4 ImageSample = tex2Dlod(Image, float4(OffsetTex, 0.0, 0.0));
            float4 GuideLowSample = tex2D(GuideLow, OffsetTex);

            // Calculate weight
            float3 Delta = GuideLowSample.xyz - GuideHighSample.xyz;
            float DotDD = dot(Delta, Delta);
            float Weight = (DotDD > 0.0) ? 1.0 / DotDD : 1.0;

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
      // Initialize variables
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float2 GuideHighSample = tex2D(Guide, Tex).xy;

      // Initialize array
      const int ImageCount = 9;
      float2 ImageSample[ImageCount];
      float2 ImageCenter;
      float2 ImageMean;
      float ImageWeight = 0.0;

      // Initialize the things to compute
      float3 Variance = 0.0;
      float2 BilateralSum = 0.0;
      float WeightSum = 0.0;

      // Calculate and store the window
      int ImageIndex = 0;

      [unroll]
      for (int dx = -1; dx <= 1; dx++)
      {
         [unroll]
         for (int dy = -1; dy <= 1; dy++)
         {
            // Calculate offset
            float2 Offset = float2(float(dx), float(dy));
            float2 OffsetTex = Tex + (Offset * PixelSize);

            // Calculate the difference and normalize it from FP16 range to [-1.0, 1.0) range
            // We normalize the difference to avoid precision loss at the higher numbers
            ImageSample[ImageIndex] = tex2Dlod(Image, float4(OffsetTex, 0.0, 0.0)).xy;

            // Contribute to the mean
            ImageMean += ImageSample[ImageIndex];
            ImageWeight += 1.0;

            if ((dx == 0) && (dy == 0))
            {
               ImageCenter = ImageSample[ImageIndex];
            }

            ImageIndex += 1;
         }
      }

      // Calculate Variance
      [unroll]
      for (int i1 = 0; i1 < ImageCount; i1++)
      {
         // Calculate the Variance (.xy) and Covariance (.z)
         float2 Difference = ImageSample[i1] - ImageMean;
         Variance.xy += (Difference * Difference);
         Variance.z += (Difference.x * Difference.y);
      }

      // Average the Mean, Variance, and Covariance here (saves MUL instructions)
      ImageMean /= ImageWeight;
      Variance /= ImageWeight;

      // Create the Coveriance matrix
      float D = (Variance.y * Variance.x) - (Variance.z * Variance.z);
      float2x2 CoverianceMat = float2x2(Variance.y, -Variance.z, -Variance.z, Variance.x) / D;

      [unroll]
      for (int i2 = 0; i2 < ImageCount; i2++)
      {
         // Calculate a Mahalanobis-like distance.
         float2 Delta1 = ImageSample[i2].xy - GuideHighSample.xy;
         float2 Delta2 = ImageSample[i2].xy - ImageCenter.xy;
         float Distance1 = dot(mul(CoverianceMat, Delta1), Delta1);
         float Distance2 = dot(mul(CoverianceMat, Delta2), Delta2);

         // Calculate weightage while avoiding division by 0.
         float Distance = (D > 0.0) ? max(Distance1, Distance2) : 1.0;
         float Weight = (Distance > 0.0) ? 1.0 / Distance : 1.0;

         BilateralSum += (ImageSample[i2] * Weight);
         WeightSum += Weight;
      }

      return BilateralSum / WeightSum;
   }
