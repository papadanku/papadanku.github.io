
Multi-Level Bilateral Upsampling on The GPU
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

      float4 ImageSum = 0.0;
      float ImageWeightSum = 0.0;
      float4 BilateralSum = 0.0;
      float BilateralWeightSum = 0.0;

      [unroll]
      for (int x = -1; x <= 1; x++)
      {
         [unroll]
         for (int y = -1; y <= 1; y++)
         {
            // Calculate offset
            float2 Offset = float2(float(x), float(y));
            float2 OffsetTex = Tex + (Offset * PixelSize);

            // Sample image and guide
            float4 ImageSample = tex2Dlod(Image, float4(OffsetTex, 0.0, 0.0));
            float4 GuideLowSample = tex2D(GuideLow, OffsetTex);

            // Calculate weight
            float4 Delta = GuideHighSample - GuideLowSample;
            float Dot4 = rsqrt(dot(Delta, Delta) + 1.0);
            float Weight = smoothstep(0.0, 1.0, Dot4);
            Weight *= Weight;

            // Accumulate sum
            ImageSum += ImageSample;
            ImageWeightSum += 1.0;

            // Accumulate bilateral
            BilateralSum += (ImageSample * Weight);
            BilateralWeightSum += Weight;
         }
      }

      ImageSum /= ImageWeightSum;
      BilateralSum = (BilateralWeightSum > 0.0) ? BilateralSum / BilateralWeightSum : ImageSum;

      return BilateralSum;
   }

Self-Guided Optimization
------------------------

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
      // Initialize variables
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);

      // Constants for Array textures
      const int ArrayCount = 9;
      int ImageIndex = 0;

      // Variables for Array textures
      float2 ImageArray[ArrayCount];
      float2 ImageCenter;

      [unroll]
      for (int x = -1; x <= 1; x++)
      {
         [unroll]
         for (int y = -1; y <= 1; y++)
         {
            // Fetch pixel
            float2 Offset = float2(float(x), float(y));
            ImageArray[ImageIndex] = tex2D(Image, Tex + (Offset * PixelSize)).xy;

            // Store the center pixel elsewhere too
            if ((x == 0) && (y == 0))
            {
               ImageCenter = ImageArray[ImageIndex];
            }

            ImageIndex += 1;
         }
      }

      // Store ImageCenter reference
      float4 Reference = float4(tex2D(Guide, Tex).xy, ImageCenter);

      // Initialize variables to compute
      float2 ImageSum = 0.0;
      float ImageWeightSum = 0.0;
      float2 BilateralSum = 0.0;
      float BilateralWeightSum = 0.0;

      [unroll]
      for (int i = 0; i < ArrayCount; i++)
      {
         // Calculate weight
         float4 Delta = ImageArray[i].xyxy - Reference;
         float MaxDot = rsqrt(dot(Delta, Delta) + 1.0);
         float Weight = smoothstep(0.0, 1.0, MaxDot);
         Weight *= Weight;

         // Accumulate sum
         ImageSum += ImageArray[i].xy;
         ImageWeightSum += 1.0;

         // Accumulate bilateral
         BilateralSum += (ImageArray[i].xy * Weight);
         BilateralWeightSum += Weight;
      }

      ImageSum /= ImageWeightSum;
      BilateralSum = (BilateralWeightSum > 0.0) ? BilateralSum / BilateralWeightSum : ImageSum;

      return BilateralSum;
   }
