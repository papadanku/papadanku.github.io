
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

Adaptive, Multi-Level, Self-Guided Side Window Bilateral Filtering
------------------------------------------------------------------

In the original multi-level bilateral filtering approach, the spatial weight is calculated using the difference between the high-resolution guide and its downsampled version. However, in scenarios where the low-resolution image and the downsampled guide share similar properties \(e.g., when the guide is derived from the image itself\), we can simplify the process by directly using the low-resolution image for calculating the spatial weight.

This modification eliminates the need for an explicit downsampled guide and can improve performance by reducing texture fetches. Using the image as a guide, we maintain the edge-preserving characteristics while optimizing the computation.

.. code-block:: hlsl
   :caption: Self-Guided Bilateral Upsampling

   /*
      This is an optimized, self-guided version for Joint Bilateral Upsampling implemented in HLSL.

      Inspired by Kopf et al. (2007) and Riemens et al. (2009).

      ---

      Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

      Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

      Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition (pp. 8758-8766).
   */

   struct SideWindowKernel
   {
      int Weights[9];
      int Size;
   };

   struct SideWindowBilateral
   {
      float2 Sum;
      float SumWeight;
   };

   void GetSideWindowBilateral(
      in SideWindowKernel Kernel,
      in float2 Guide,
      in float2 ImageArray[9],
      out SideWindowBilateral Output
   )
   {
      // Constants: Mean
      const int KernelSize = 9;
      const float Epsilon = 1e-7;
      const float MeanN = 1.0 / Kernel.Size;
      const float VarianceN = 1.0 / (Kernel.Size - 1.0);

      // Initialize variance data
      float2 Mean = 0.0;
      float Variance = Epsilon;

      for (int i0 = 0; i0 < KernelSize; i0++)
      {
         if (Kernel.Weights[i0] == 1)
         {
            Mean += (ImageArray[i0] * MeanN);
         }
      }

      for (int i1 = 0; i1 < KernelSize; i1++)
      {
         if (Kernel.Weights[i1] == 1)
         {
            float2 D = ImageArray[i1] - Mean;
            Variance += (dot(D, D) * VarianceN);
         }
      }

      // Initialize output data
      int ImageIndex = 0;
      Output.Sum = 0.0;
      Output.SumWeight = 0.0;

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            // Compute Weight (Spatial)
            float2 Offset = float2(x, y);
            float DistSqSpatial = dot(Offset, Offset);
            float WeightS = 1.0 / (DistSqSpatial + Variance);

            // Compute Weight (Range)
            float2 Delta = ImageArray[ImageIndex] - Guide;
            float DistSqRange = dot(Delta, Delta);
            float WeightR = 1.0 / (DistSqRange + 1.0);

            float Weight = WeightS * WeightR;
            Output.Sum += (ImageArray[ImageIndex] * Weight);
            Output.SumWeight += Weight;

            ImageIndex += 1;
         }
      }
   }

   float2 GetSelfBilateralUpsampleXY(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex
   )
   {
      // Precompute (constants)
      const int ArrayCount = 9;
      const int KernelSizeSide = 6;
      const int KernelSizeCorner = 4;

      // Precompute (static)
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float2 GuideTexture = tex2D(Guide, Tex).xy;

      float2 ImageArray[ArrayCount];
      float2 Reference;
      int ImageIndex = 0;

      /*
         Gather samples

         0 1 2   (North-West  |  North  |  North-East)
         3 4 5   (   West     |  Center |     East   )
         6 7 8   (South-West  |  South  |  South-East)
      */

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            float2 Offset = Tex + (float2(x, y) * PixelSize);
            ImageArray[ImageIndex] = tex2D(Image, Offset).xy;

            if ((x == 0) && y == 0)
            {
               Reference = ImageArray[ImageIndex];
            }

            ImageIndex += 1;
         }
      }

      // Construct array of kernels
      SideWindowKernel Kernel[8];
      Kernel[0].Weights = { 1, 1, 1,  1, 1, 1,  0, 0, 0 }; // Row 0 & 1 (N)
      Kernel[0].Size = KernelSizeSide;
      Kernel[1].Weights = { 0, 0, 0,  1, 1, 1,  1, 1, 1 }; // Row 1 & 2 (S)
      Kernel[1].Size = KernelSizeSide;
      Kernel[2].Weights = { 1, 1, 0,  1, 1, 0,  1, 1, 0 }; // Col 0 & 1 (E)
      Kernel[2].Size = KernelSizeSide;
      Kernel[3].Weights = { 0, 1, 1,  0, 1, 1,  0, 1, 1 }; // Col 1 & 2 (W)
      Kernel[3].Size = KernelSizeSide;
      Kernel[4].Weights = { 1, 1, 0,  1, 1, 0,  0, 0, 0 }; // Rows 0,1 & Cols 0,1 (NW)
      Kernel[4].Size = KernelSizeCorner;
      Kernel[5].Weights = { 0, 1, 1,  0, 1, 1,  0, 0, 0 }; // Rows 0,1 & Cols 1,2 (NE)
      Kernel[5].Size = KernelSizeCorner;
      Kernel[6].Weights = { 0, 0, 0,  1, 1, 0,  1, 1, 0 }; // Rows 1,2 & Cols 0,1 (SW)
      Kernel[6].Size = KernelSizeCorner;
      Kernel[7].Weights = { 0, 0, 0,  0, 1, 1,  0, 1, 1 }; // Rows 1,2 & Cols 1,2 (SE)
      Kernel[7].Size = KernelSizeCorner;

      // Calculate Side Winder filter
      float2 Mean = Reference;
      bool AVariance = false;
      float Variance = 0.0;

      [unroll]
      for (int i = 0; i < 8; i++)
      {
         SideWindowBilateral SideWindow;
         GetSideWindowBilateral(Kernel[i], GuideTexture, ImageArray, SideWindow);

         // Avoid division by zero on empty/low weight regions
         if (SideWindow.SumWeight > 0.0)
         {
            float2 WindowMean = SideWindow.Sum / SideWindow.SumWeight;
            float2 Delta = WindowMean - Reference;
            float WindowVariance = dot(Delta, Delta);

            if (!AVariance || (WindowVariance < Variance))
            {
               AVariance = true;
               Variance = WindowVariance;
               Mean = WindowMean;
            }
         }
      }

      return Mean;
   }
