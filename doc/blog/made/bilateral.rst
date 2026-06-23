
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

The algorithm evaluates multiple side windows, covering cardinal directions and corners. Instead of selecting a single optimal window, it combines their results using a variance-weighted average. This "soft-selection" approach allows the filter to prioritize windows that align with local edges while still incorporating information from neighboring regions.

The SWF framework supports various filter implementations:

Box Filter
   Computes the arithmetic mean of all pixels within the side window.

Gaussian Filter
   Applies a weighted average where pixels closer to the target pixel contribute more.

Median Filter
   Selects the median value from the window, which effectively removes noise while maintaining edge sharpness.

Bilateral Filter
   Weights pixels based on both spatial distance and intensity difference. This ensures that only pixels with similar values contribute to the result.

The implemented version follows a step-by-step process:

#. **Kernel Generation**: Define a set of kernels representing eight side windows: four cardinal directions and four corners.
#. **Window Statistics Calculation**: For each window, compute the local mean :math:`\mu_W` and variance :math:`\sigma^2_W`.
#. **Bilateral Weighted Estimation**: For each window, calculate a bilateral-weighted mean :math:`\mu_{W, \text{bilat}}`. The range weight is adaptively adjusted using the window's variance :math:`\sigma^2_W`:

   .. math::

      w_r = \frac{1}{1 + \|d\|^2 + \sigma^2_W}

#. **Variance-Weighted Combination**: Combine the estimated means using their inverse variances as weights:

   .. math::

      \mu_{\text{final}} = \frac{\sum \mu_{W_i, \text{bilat}} \cdot \frac{1}{\sigma^2_{W_i}}}{\sum \frac{1}{\sigma^2_{W_i}}}

.. note:: Why Variance-Weighted Averaging?

   Instead of selecting a single window that minimizes variance (a "hard" selection), this algorithm uses the inverse of the local variance as a weight to combine all side windows. This "soft-selection" approach allows the filter to prioritize windows that align with local edges while still incorporating information from neighboring regions.

Karis Averaging for Motion Vectors
----------------------------------

In temporal upsampling, "pulsation" occurs when a filter's choice jumps abruptly between different windows across frames. A standard minimum-variance selection can be too sensitive to noise, causing these sudden jumps.

To mitigate this, we implement a technique similar to Karis averaging. While Karis averaging typically uses pixel brightness to prevent over-brightening, we use the sum of pixel variances to infer stability. This ensures that the contribution of each side window is proportional to its local stability, leading to much smoother and more coherent upsampled motion vectors.

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
   :caption: Variance-Weighted Adaptive, Multilevel, Side-Window Bilateral Upsampling

   /*
      This is an optimized, self-guided version for Joint Bilateral Upsampling implemented in HLSL.

      Inspired by Kopf et al. (2007) and Riemens et al. (2009).

      ---

      Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

      Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

      Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition (pp. 8758-8766).
   */

   struct SharedData_SideWindowBilateral
   {
      // Shared constants
      int ArrayImageSize;
      int SideWindowSize_Corner;
      int SideWindowSize_Cardinal;

      // Shared between side windows
      float2 ArrayImages[9];
      float ArrayDistances[9];
      float2 SideWindowMeans[8];

      // Shared for final calculation
      float2 Reference;
   };

   struct SideWindow_Bilateral
   {
      float Masks[9];
      float Size;
      float2 Sum;
      float SumWeight;
      float IVariance;
   };

   void GetSharedData_SideWindowBilateral(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex,
      out SharedData_SideWindowBilateral Output
   )
   {
      // Precompute constants (side windows)
      Output.SideWindowSize_Corner = 4;
      Output.SideWindowSize_Cardinal = 6;

      // Initialize variables
      Output.ArrayImageSize = 9;
      Output.ArrayImages[Output.ArrayImageSize];
      Output.ArrayDistances[Output.ArrayImageSize];
      Output.Reference;

      // Precompute (static)
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float2 GuideTexture = tex2D(Guide, Tex).xy;

      /*
         Gather samples:

         0 1 2 [ North West | North  | North East ]
         3 4 5 [    West    | Center |    East    ]
         6 7 8 [ South West | South  | South East ]
      */

      int ImageIndex = 0;

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            float2 Offset = Tex + (float2(x, y) * PixelSize);
            float2 Sample = tex2D(Image, Offset).xy;
            float2 Delta = Sample - GuideTexture;
            Output.ArrayImages[ImageIndex] = Sample;
            Output.ArrayDistances[ImageIndex] = dot(Delta, Delta);

            if ((x == 0) && (y == 0))
            {
               Output.Reference = Sample;
            }

            ImageIndex += 1;
         }
      }

      /*
         Construct array of kernels:

         [0] [1] [2]  (Top Row)
         [3] [4] [5]  (Mid Row)
         [6] [7] [8]  (Bot Row)

         NORTH   SOUTH   EAST    WEST
         x x x   - - -   - x x   x x -
         x x x   x x x   - x x   x x -
         - - -   x x x   - x x   x x -

         NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
         x x -       - x x       - - -       - - -
         x x -       - x x       x x -       - x x
         - - -       - - -       x x -       - x x
      */

      const float SideWindowWeight_Corner = 1.0 / float(Output.SideWindowSize_Corner);
      const float SideWindowWeight_Cardinal = 1.0 / float(Output.SideWindowSize_Cardinal);

      float2 Submeans[8];
      Submeans[0] = Output.ArrayImages[0].xy + Output.ArrayImages[3].xy; // Vertical-Top-Left
      Submeans[1] = Output.ArrayImages[1].xy + Output.ArrayImages[4].xy; // Vertical-Top-Mid
      Submeans[2] = Output.ArrayImages[2].xy + Output.ArrayImages[5].xy; // Vertical-Top-Right
      Submeans[3] = Output.ArrayImages[3].xy + Output.ArrayImages[6].xy; // Vertical-Bottom-Left
      Submeans[4] = Output.ArrayImages[4].xy + Output.ArrayImages[7].xy; // Vertical-Bottom-Mid
      Submeans[5] = Output.ArrayImages[5].xy + Output.ArrayImages[8].xy; // Vertical-Bottom-Right
      Submeans[6] = Output.ArrayImages[6].xy + Output.ArrayImages[7].xy; // Horizontal-Bottom-Left
      Submeans[7] = Output.ArrayImages[7].xy + Output.ArrayImages[8].xy; // Horizontal-Bottom-Right

      Output.SideWindowMeans[0] = Submeans[0] + Submeans[1]; // NW: [0 + 3] + [1 + 4]
      Output.SideWindowMeans[1] = Submeans[1] + Submeans[2]; // NE: [1 + 4] + [2 + 5]
      Output.SideWindowMeans[2] = Submeans[3] + Submeans[4]; // SW: [3 + 6] + [4 + 7]
      Output.SideWindowMeans[3] = Submeans[4] + Submeans[5]; // SE: [4 + 7] + [5 + 8]
      Output.SideWindowMeans[4] = Output.SideWindowMeans[0] + Submeans[2]; // N: [0 + 3 + 1 + 4] + [2 + 5]
      Output.SideWindowMeans[5] = Output.SideWindowMeans[2] + Submeans[5]; // S: [3 + 6 + 4 + 7] + [5 + 8]
      Output.SideWindowMeans[6] = Output.SideWindowMeans[0] + Submeans[6]; // W: [0 + 3 + 1 + 4] + [6 + 7]
      Output.SideWindowMeans[7] = Output.SideWindowMeans[1] + Submeans[7]; // E: [1 + 4 + 2 + 5] + [7 + 8]

      Output.SideWindowMeans[0] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[1] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[2] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[3] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[4] *= SideWindowWeight_Cardinal;
      Output.SideWindowMeans[5] *= SideWindowWeight_Cardinal;
      Output.SideWindowMeans[6] *= SideWindowWeight_Cardinal;
      Output.SideWindowMeans[7] *= SideWindowWeight_Cardinal;
   }

   void GetSideWindowBilateral(
      in SharedData_SideWindowBilateral Input,
      in float2 Mean,
      inout SideWindow_Bilateral Block
   )
   {
      // Pre-compute Spatial distances
      // .x = Center (0 + 0); .y = Diagonal (1 + 1); .z = Cardinal (0 + 1)
      const float3 SpatialDistances = exp2(-float3(0.0, 1.0, 2.0));
      const float VarianceN = 1.0 / (float(Block.Size) - 1.0);

      // Initialize output members
      Block.Sum = 0.0;
      Block.SumWeight = 0.0;

      /*
         We initialize by 1 for the following reasons:

         1. Range weighting: Done with Lorentzian approximation

            x / (1 + x)

         2. Compute the inverted variance: Used for variance weighting

            1 / (1 + v)
      */

      float Variance = 1.0;

      // Compute the SideWindow's variance
      [unroll]
      for (int i1 = 0; i1 < Input.ArrayImageSize; i1++)
      {
         if (Block.Masks[i1] == 1)
         {
            float2 D = Input.ArrayImages[i1] - Mean;
            Variance += (dot(D, D) * VarianceN);
         }
      }

      // Initialize Outputs
      int ImageIndex = 0;

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            if (Block.Masks[ImageIndex] == 1)
            {
               // Compute Weight (Range)
               float DistSqRange = Input.ArrayDistances[ImageIndex];
               float WeightRange = 1.0 / (DistSqRange + Variance);

               // Compute Weight (Spatial)
               int SpatialOffset = abs(x) + abs(y);
               float WeightSpatial = SpatialDistances[SpatialOffset];
               float Weight = WeightSpatial * WeightRange;

               // Accumulate
               Block.Sum += (Input.ArrayImages[ImageIndex] * Weight);
               Block.SumWeight += Weight;
            }

            ImageIndex += 1;
         }
      }

      Block.IVariance = 1.0 / Variance;
   }

   float2 GetSelfBilateralUpsampleFLT2(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex
   )
   {
      const int SideWindowsCount = 8;

      // Create the data struct that we will use accross multiple functions.
      SharedData_SideWindowBilateral SharedData;
      GetSharedData_SideWindowBilateral(Image, Guide, Tex, SharedData);

      // Initialize our side windows
      SideWindow_Bilateral SideWindows[SideWindowsCount];
      SideWindows[0].Masks = { 1, 1, 0,  1, 1, 0,  0, 0, 0 }; // NW
      SideWindows[0].Size = SharedData.SideWindowSize_Corner;
      SideWindows[1].Masks = { 0, 1, 1,  0, 1, 1,  0, 0, 0 }; // NE
      SideWindows[1].Size = SharedData.SideWindowSize_Corner;
      SideWindows[2].Masks = { 0, 0, 0,  1, 1, 0,  1, 1, 0 }; // SW
      SideWindows[2].Size = SharedData.SideWindowSize_Corner;
      SideWindows[3].Masks = { 0, 0, 0,  0, 1, 1,  0, 1, 1 }; // SE
      SideWindows[3].Size = SharedData.SideWindowSize_Corner;
      SideWindows[4].Masks = { 1, 1, 1,  1, 1, 1,  0, 0, 0 }; // N
      SideWindows[4].Size = SharedData.SideWindowSize_Cardinal;
      SideWindows[5].Masks = { 0, 0, 0,  1, 1, 1,  1, 1, 1 }; // S
      SideWindows[5].Size = SharedData.SideWindowSize_Cardinal;
      SideWindows[6].Masks = { 1, 1, 0,  1, 1, 0,  1, 1, 0 }; // W
      SideWindows[6].Size = SharedData.SideWindowSize_Cardinal;
      SideWindows[7].Masks = { 0, 1, 1,  0, 1, 1,  0, 1, 1 }; // E
      SideWindows[7].Size = SharedData.SideWindowSize_Cardinal;

      /*
         Calculate the variance-weighted Side Window filter. This may sound strange, but it works better than the regular min(x) method.

         While Google's enterprise-class clanker suggested this method, I did my discernment and revised it to work like do CBloom's Karis averaging. In layman's terms, a Karis average means "we will add 4 things together: darken the very-bright things and keep the not-very-bright-things the same". The "thing" is either a single pixel (for a Full Karis Average) or a sum of pixels (for a Partial Karis Average). We use the Karis average to prevent pulsating regions when downsampling.

         What about motion vectors? Instead of measuring the sum of pixel brightness to infer pulsating areas, we use the sum of pixel variances.
      */

      float2 WindowMean = 0.0;
      float SumIVariance = 0.0;

      [unroll]
      for (int i0 = 0; i0 < SideWindowsCount; i0++)
      {
         GetSideWindowBilateral(SharedData, SharedData.SideWindowMeans[i0], SideWindows[i0]);
         SideWindows[i0].Sum /= SideWindows[i0].SumWeight;

         // Weighted sum by variance
         WindowMean += (SideWindows[i0].Sum * SideWindows[i0].IVariance);
         SumIVariance += SideWindows[i0].IVariance;
      }

      WindowMean = WindowMean / SumIVariance;

      return WindowMean;
   }
