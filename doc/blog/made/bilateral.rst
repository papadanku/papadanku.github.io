
Multilevel Adaptive Side-Window Bilateral Upsampling on the GPU
===============================================================

This is my proposal for an Adaptive, Multilevel, Side-Window Bilateral Upsampling filter for motion vectors.

.. seealso::

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

   Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

   Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 8758-8766.

Bilateral Upsampling
--------------------

Bilateral upsampling leverages a high-resolution guide image to interpolate a low-resolution target image. Unlike standard linear interpolation, which assumes a smoothness prior, this technique uses the guide image to determine where edges occur.

The filter computes a weighted average of nearby low-resolution pixels. The weight for each pixel depends on two factors:

#. **Spatial Distance**: Pixels closer to the target location contribute more.
#. **Intensity Difference**: Pixels in the guide image with similar intensities to the target guide pixel contribute more.

This dual-weighting ensures that only pixels on the same side of an edge contribute to the result, effectively preserving structural boundaries.

Using Adaptive Weights
----------------------

Adaptive bilateral upsampling improves the process by dynamically adjusting the filter's sensitivity based on local image characteristics. Instead of using global constants for the range variance, the algorithm calculates local variances within the filtering window.

In regions with low variance (homogeneous areas), the filter allows a wider range of pixels to contribute, enhancing smoothing. In regions with high variance (edges), the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures that the filter's strength is proportional to the local content's complexity.

Using the Side Window Filter
----------------------------

Conventional filtering algorithms center the local window on the target pixel. When a pixel lies near an edge, this centered window captures samples from both sides of the boundary. Averaging these dissimilar pixels blurs the edge.

The algorithm evaluates multiple side windows, covering cardinal directions and corners, and selects the optimal window that minimizes the difference between the filtered mean and the reference pixel. By aligning the window boundary with the edge, the filter avoids sampling pixels from the opposite side of a boundary.

The SWF framework supports various filter implementations:

Box Filter
   Computes the arithmetic mean of all pixels within the side window.

Gaussian Filter
   Applies a weighted average where pixels closer to the target pixel contribute more.

Median Filter
   Selects the median value from the window, which effectively removes noise while maintaining edge sharpness.

Bilateral Filter
   Weights pixels based on both spatial distance and intensity difference. This ensures that only pixels with similar values contribute to the result.

The implemented version follows a step-by-step process to select the most appropriate side window:

#. **Kernel Generation**: Define a set of kernels representing eight side windows: four cardinal directions and four corners.
#. **Window Statistics Calculation**: For each window, compute the local mean :math:`\mu_W` and variance :math:`\sigma^2_W`.
#. **Bilateral Weighted Estimation**: For each window, calculate a bilateral-weighted mean :math:`\mu_{W, \text{bilat}}`. The range weight is adaptively adjusted using the window's variance :math:`\sigma^2_W`:

   .. math::

      w_r = \frac{1}{1 + \|d\|^2 + \sigma^2_W}

#. **Optimal Window Selection**: Compare the bilateral mean of each window to the target reference pixel :math:`p`. Select the window that minimizes the squared distance:

   .. math::

      W^* = \arg\min_{W_i} \| \mu_{W_i, \text{bilat}} - p \|^2

Using Image Pyramids
--------------------

A multilevel scheme uses an image pyramid for recursive upsampling. Rather than performing a single large upsampling step, the algorithm increases resolution in multiple stages (e.g., :math:`2 \times 2` at each step).

At each level of the pyramid, the adaptive side-window bilateral filter is applied to the current resolution. This recursive refinement prevents aliasing artifacts and reduces the computational cost compared to a single-step high-resolution filter.

Multilevel Adaptive Side-Window Bilateral Upsampling
----------------------------------------------------

The technique builds upon bilateral upsampling using the following:

- **Adaptive Weighting**: The filter's range parameters are adjusted based on local image variance.
- **Side Window Filtering**: Evaluating multiple shifted windows and selecting the one that best aligns with the target pixel.
- **Image Pyramids**: Recursive upsampling to reduce computational cost.

.. code-block:: hlsl
   :caption: Self-Guided, Adaptive, Multilevel, Side-Window Bilateral Upsampling

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
      const float Epsilon = 1.0;
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

      // Pre-compute Spatial distances
      // .x = Center (0 + 0); .y = Diagonal (1 + 1); .z = Cardinal (0 + 1)
      float3 SpatialDistances = exp2(-float3(0.0, 1.0, 2.0));

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            if (Kernel.Weights[ImageIndex] == 1)
            {
               // Compute Weight (Range)
               float2 Delta = ImageArray[ImageIndex] - Guide;
               float DistSqRange = dot(Delta, Delta);
               float WeightRange = 1.0 / (DistSqRange + Variance);

               // Compute Weight (Spatial)
               int SpatialOffset = abs(x) + abs(y);
               float WeightSpatial = SpatialDistances[SpatialOffset];

               /*
                  Defer the reciprocal. The following are identical:

                  (1 / a) * (1 / b)
                  1 / (a * b)
               */
               float Weight = WeightSpatial * WeightRange;

               // Accumulate
               Output.Sum += (ImageArray[ImageIndex] * Weight);
               Output.SumWeight += Weight;
            }

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
         Gather samples:

         0 1 2 [ North West | North  | North East ]
         3 4 5 [    West    | Center |    East    ]
         6 7 8 [ South West | South  | South East ]
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

      /*
         Construct array of kernels:

         NORTH   SOUTH   EAST    WEST
         x x x   - - -   - x x   x x -
         x x x   x x x   - x x   x x -
         - - -   x x x   - x x   x x -

         NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
         x x -       - x x       - - -       - - -
         x x -       - x x       x x -       - x x
         - - -       - - -       x x -       - x x
      */

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
