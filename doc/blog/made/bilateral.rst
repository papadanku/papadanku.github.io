
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

The algorithm evaluates multiple side windows, covering cardinal directions and corners, and selects the optimal window that minimizes the local variance. By aligning the window boundary with the edge, the filter avoids sampling pixels from the opposite side of a boundary.

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

#. **Optimal Window Selection**: Select the window that minimizes the local variance :math:`\sigma^2_W`:

   .. math::

      W^* = \arg\min_{W_i} \sigma^2_{W_i}`

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

   struct SideWindowBlockBilateral
   {
      float2 Mean;
      float Variance;
      int Weights[9];
   };

   struct SideWindowBilateral
   {
      float2 Sum;
      float SumWeight;
   };

   void InitSideWindowBilateral(
      in int SubwindowSize,
      in float3 ImageArray[9],
      in float2 Mean,
      inout SideWindowBlockBilateral Block)
   {
      const int ImageArraySize = 9;
      const float MeanN = 1.0 / float(SubwindowSize);
      const float VarianceN = 1.0 / (float(SubwindowSize) - 1.0);

      // Compute Mean
      Block.Mean = Mean * MeanN;

      // Initialize variance data
      Block.Variance = 0.0;

      [unroll]
      for (int i1 = 0; i1 < ImageArraySize; i1++)
      {
         if (Block.Weights[i1] == 1)
         {
            float2 D = ImageArray[i1].xy - Block.Mean;
            Block.Variance += (dot(D, D) * VarianceN);
         }
      }
   }

   void GetSideWindowBilateral(
      in float3 ImageArray[9],
      in SideWindowBlockBilateral Block,
      out SideWindowBilateral Output
   )
   {
      // Initialize output data
      int ImageIndex = 0;

      // Initialize Outputs
      float VarD = 1.0 + Block.Variance;
      float2 Sum = 0.0;
      float WSum = 0.0;

      // Pre-compute Spatial distances
      // .x = Center (0 + 0); .y = Diagonal (1 + 1); .z = Cardinal (0 + 1)
      float3 SpatialDistances = exp2(-float3(0.0, 1.0, 2.0));

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            if (Block.Weights[ImageIndex] == 1)
            {
               // Compute Weight (Range)
               float DistSqRange = ImageArray[ImageIndex].z;
               float WeightRange = 1.0 / (DistSqRange + VarD);

               // Compute Weight (Spatial)
               int SpatialOffset = abs(x) + abs(y);
               float WeightSpatial = SpatialDistances[SpatialOffset];
               float Weight = WeightSpatial * WeightRange;

               // Accumulate
               Sum += (ImageArray[ImageIndex].xy * Weight);
               WSum += Weight;
            }

            ImageIndex += 1;
         }
      }

      Output.Sum = Sum;
      Output.SumWeight = WSum;
   }

   float2 GetSelfBilateralUpsampleXY(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex
   )
   {
      // Precompute (constants)
      const int ArrayCount = 9;

      // Precompute (static)
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float2 GuideTexture = tex2D(Guide, Tex).xy;
      float2 Reference;

      float3 ImageArray[ArrayCount];
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
            float2 Sample = tex2D(Image, Offset).xy;
            float2 Delta = Sample - GuideTexture;
            ImageArray[ImageIndex].xy = Sample;
            ImageArray[ImageIndex].z = dot(Delta, Delta);

            if ((x == 0) && (y == 0))
            {
               Reference = ImageArray[ImageIndex].xy;
            }

            ImageIndex += 1;
         }
      }

      /*
         [0] [1] [2]  (Top Row)
         [3] [4] [5]  (Mid Row)
         [6] [7] [8]  (Bot Row)

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

      float2 Submean[8];
      Submean[0] = ImageArray[0].xy + ImageArray[3].xy; // Vertical-Top-Left
      Submean[1] = ImageArray[1].xy + ImageArray[4].xy; // Vertical-Top-Mid
      Submean[2] = ImageArray[2].xy + ImageArray[5].xy; // Vertical-Top-Right
      Submean[3] = ImageArray[3].xy + ImageArray[6].xy; // Vertical-Bottom-Left
      Submean[4] = ImageArray[4].xy + ImageArray[7].xy; // Vertical-Bottom-Mid
      Submean[5] = ImageArray[5].xy + ImageArray[8].xy; // Vertical-Bottom-Right
      Submean[6] = ImageArray[6].xy + ImageArray[7].xy; // Horizontal-Bottom-Left
      Submean[7] = ImageArray[7].xy + ImageArray[8].xy; // Horizontal-Bottom-Right

      float2 Mean[8];
      Mean[0] = Submean[0] + Submean[1]; // NW (0+3 + 1+4)
      Mean[1] = Submean[1] + Submean[2]; // NE (1+4 + 2+5)
      Mean[2] = Submean[3] + Submean[4]; // SW (3+6 + 4+7)
      Mean[3] = Submean[4] + Submean[5]; // SE (4+7 + 5+8)
      Mean[4] = Mean[0] + Submean[2]; // N (0+3+1+4 + 2+5)
      Mean[5] = Mean[2] + Submean[5]; // S (3+6+4+7 + 5+8)
      Mean[6] = Mean[0] + Submean[6]; // W (0+3+1+4 + 6+7)
      Mean[7] = Mean[1] + Submean[7]; // E (1+4+2+5 + 7+8)

      const int SideWindowAmount = 8;
      const int SubwindowSizes[SideWindowAmount] = { 4, 4, 4, 4, 6, 6, 6, 6 };
      const int StaticWeightsLength = 9;
      const int StaticWeights[StaticWeightsLength * SideWindowAmount] =
      {
         1, 1, 0,  1, 1, 0,  0, 0, 0, // NW (0-8)
         0, 1, 1,  0, 1, 1,  0, 0, 0, // NE (9-17)
         0, 0, 0,  1, 1, 0,  1, 1, 0, // SW (18-26)
         0, 0, 0,  0, 1, 1,  0, 1, 1, // SE (27-35)
         1, 1, 1,  1, 1, 1,  0, 0, 0, // N  (36-44)
         0, 0, 0,  1, 1, 1,  1, 1, 1, // S  (45-53)
         1, 1, 0,  1, 1, 0,  1, 1, 0, // W  (54-62)
         0, 1, 1,  0, 1, 1,  0, 1, 1  // E  (63-71)
      };

      // Initialize our side windows
      SideWindowBlockBilateral Blocks[SideWindowAmount];

      [unroll]
      for (int i0 = 0; i0 < SideWindowAmount; i0++)
      {
         [unroll]
         for (int i1 = 0; i1 < StaticWeightsLength; i1++)
         {
            int ID = (i0 * StaticWeightsLength) + i1;
            Blocks[i0].Weights[i1] = StaticWeights[ID];
         }

         InitSideWindowBilateral(SubwindowSizes[i0], ImageArray, Mean[i0], Blocks[i0]);
      }

      // Calculate Side Winder filter
      float2 NearestWindow = Reference;
      bool AVariance = false;
      float Variance = 0.0;

      [unroll]
      for (int i2 = 0; i2 < SideWindowAmount; i2++)
      {
         SideWindowBilateral SideWindow;
         GetSideWindowBilateral(ImageArray, Blocks[i2], SideWindow);

         if (SideWindow.SumWeight > 0.0)
         {
            if (!AVariance || (Blocks[i2].Variance < Variance))
            {
               AVariance = true;
               Variance = Blocks[i2].Variance;
               NearestWindow = SideWindow.Sum / SideWindow.SumWeight;
            }
         }
      }

      return NearestWindow;
   }
