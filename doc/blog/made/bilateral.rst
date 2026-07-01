
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

Adaptive bilateral upsampling improves the process by dynamically adjusting the filter's sensitivity based on local image characteristics. Instead of using global constants for the range variance, the algorithm calculates variances within the filtering window at two different scales: the global window and the individual side windows.

In regions with low variance (homogeneous areas), the filter allows a wider range of pixels to contribute, enhancing smoothing. In regions with high variance (edges), the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures that the filter's strength is proportional to the local content's complexity.

Global Window: MAD-based Variance
---------------------------------

To determine the overall range sensitivity, the filter computes the Median Absolute Deviation (MAD) across the entire local window. The MAD provides a robust estimate of the local variance that is less sensitive to outliers than standard variance. It is defined as:

.. math::

   MAD = \text{median}(|x_i - \text{median}(x)|)

This MAD value is used to adapt the range weights, ensuring that the filter responds appropriately to the overall local texture:

.. math::

   w_r = \frac{1}{1 + \|d\|^2 + \sigma^2_{\text{MAD}}}

Side Windows: Sample Variance Weighting
----------------------------------------

For the "soft-selection" of side windows, the filter calculates the standard sample variance for each window. This allows the algorithm to weight windows based on their local stability. The sample variance $s^2$ for a window of size $N$ is computed as:

.. math::

   s^2 = \frac{1}{N-1} \sum_{i=1}^{N} (x_i - \bar{x})^2

where $\bar{x}$ is the sample mean of the window. The inverse of this variance, adjusted via a Lorentzian approximation, is used to weight the contribution of each side window:

.. math::

   w_v = \frac{1}{1 + s^2}

Using the Side Window Filter
----------------------------

Conventional filtering algorithms center the local window on the target pixel. When a pixel lies near an edge, this centered window captures samples from both sides of the boundary. Averaging these dissimilar pixels blurs the edge.

The algorithm evaluates multiple side windows, covering cardinal directions and corners. Instead of selecting a single optimal window, it combines their results using the sample variance-weighted average described in the :ref:`side_window_variance` section. This "soft-selection" approach allows the filter to prioritize windows that align with local edges while still incorporating information from neighboring regions.

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
      3x3 Median
      Morgan McGuire and Kyle Whitson
      http://graphics.cs.williams.edu

      Copyright (c) Morgan McGuire and Williams College, 2006
      All rights reserved.

      Redistribution and use in source and binary forms, with or without
      modification, are permitted provided that the following conditions are
      met:

      Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.

      Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

      THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
      "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
      LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
      A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
      HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
      SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
      LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
      DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
      THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
      (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
      OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
   */

   #define MEDIAN_SWAP2(A, B) \
      Temp = A; \
      A = min(A, B); \
      B = max(Temp, B); \

   #define MEDIAN_MN3(A, B, C) \
      MEDIAN_SWAP2(A, B); \
      MEDIAN_SWAP2(A, C); \

   #define MEDIAN_MX3(A, B, C) \
      MEDIAN_SWAP2(B, C); \
      MEDIAN_SWAP2(A, C); \

   // 3 exchanges
   #define MEDIAN_MNMX3(A, B, C) \
      MEDIAN_MX3(A, B, C); \
      MEDIAN_SWAP2(A, B); \

   // 4 exchanges
   #define MEDIAN_MNMX4(A, B, C, D) \
      MEDIAN_SWAP2(A, B); \
      MEDIAN_SWAP2(C, D); \
      MEDIAN_SWAP2(A, C); \
      MEDIAN_SWAP2(B, D); \

   // 6 exchanges
   #define MEDIAN_MNMX5(A, B, C, D, E) \
      MEDIAN_SWAP2(A, B); \
      MEDIAN_SWAP2(C, D); \
      MEDIAN_MN3(A, C, E); \
      MEDIAN_MX3(B, D, E); \

   // 7 exchanges
   #define MEDIAN_MNMX6(A, B, C, D, E, F) \
      MEDIAN_SWAP2(A, D); \
      MEDIAN_SWAP2(B, E); \
      MEDIAN_SWAP2(C, F); \
      MEDIAN_MN3(A, B, C); \
      MEDIAN_MX3(D, E, F); \

   // Starting with a subset of size 6, remove the min and max each time
   #define MEDIAN_3x3(DATA_TYPE, ARRAY_3x3) \
      DATA_TYPE Temp; \
      MEDIAN_MNMX6(ARRAY_3x3[0], ARRAY_3x3[1], ARRAY_3x3[2], ARRAY_3x3[3], ARRAY_3x3[4], ARRAY_3x3[5]); \
      MEDIAN_MNMX5(ARRAY_3x3[1], ARRAY_3x3[2], ARRAY_3x3[3], ARRAY_3x3[4], ARRAY_3x3[6]); \
      MEDIAN_MNMX4(ARRAY_3x3[2], ARRAY_3x3[3], ARRAY_3x3[4], ARRAY_3x3[7]); \
      MEDIAN_MNMX3(ARRAY_3x3[3], ARRAY_3x3[4], ARRAY_3x3[8]); \

   #define TEMPLATE_CBLUR_GETMEDIAN3X3(DATA_TYPE, LENGTH) \
      DATA_TYPE GetMedian3x3FLT##LENGTH(DATA_TYPE Array[9]) \
      { \
         MEDIAN_3x3(DATA_TYPE, Array) \
         return Array[4]; \
      } \

   TEMPLATE_CBLUR_GETMEDIAN3X3(float, 1)
   TEMPLATE_CBLUR_GETMEDIAN3X3(float2, 2)
   TEMPLATE_CBLUR_GETMEDIAN3X3(float3, 3)
   TEMPLATE_CBLUR_GETMEDIAN3X3(float4, 4)

   // Create an array of Median Differences
   #define TEMPLATE_CBLUR_GETMAD3x3(DATA_TYPE, LENGTH) \
      DATA_TYPE GetMAD3x3FLT##LENGTH(DATA_TYPE Array[9]) \
      { \
         DATA_TYPE Median = GetMedian3x3FLT##LENGTH(Array); \
         DATA_TYPE MedianDeltas[9]; \
         \
         [unroll] \
         for (int i = 0; i < 9; i++) \
         { \
            DATA_TYPE D = Array[i] - Median; \
            MedianDeltas[i] = dot(abs(D), 1.0); \
         } \
         \
         return GetMedian3x3FLT##LENGTH(MedianDeltas); \
      } \

   TEMPLATE_CBLUR_GETMAD3x3(float, 1)
   TEMPLATE_CBLUR_GETMAD3x3(float2, 2)
   TEMPLATE_CBLUR_GETMAD3x3(float3, 3)
   TEMPLATE_CBLUR_GETMAD3x3(float4, 4)

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
      int ArrayImageLength;
      int SideWindowSize_Corner;
      int SideWindowSize_Cardinal;

      // Shared between side windows
      float2 ArrayImages[9];
      float ArrayDistances[9];
      float2 SideWindowMeans[8];
      float GVariance;

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
      const int ArrayImageLength = 9;
      const int SideWindowSize_Corner = 4;
      const int SideWindowSize_Cardinal = 6;

      // Precompute constants (side windows)
      Output.SideWindowSize_Corner = SideWindowSize_Corner;
      Output.SideWindowSize_Cardinal = SideWindowSize_Cardinal;

      // Initialize variables
      Output.ArrayImageLength = ArrayImageLength;
      Output.Reference;

      // Precompute (static)
      float2 PixelSize = ldexp(fwidth(Tex.xy), 1.0);
      float2 GuideTexture = tex2D(Guide, Tex).xy;

      /*
         Gather samples:

         0 3 6 [ North West | North  | North East ]
         1 4 7 [    West    | Center |    East    ]
         2 5 8 [ South West | South  | South East ]
      */

      int ImageIndex = 0;

      [unroll]
      for (int x = -1; x <= 1; x++)
      {
         [unroll]
         for (int y = -1; y <= 1; y++)
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
         Compute the Median of Absolute Deviation (MAD)
      */

      // Initialize the arrays that will be used to calculate the MAD
      float2 MedianArray[ArrayImageLength];
      float MedianDeltas[ArrayImageLength];

      // Copy information from Output.ArrayImages into MedianArray
      for (int i0 = 0; i0 < ArrayImageLength; i0++)
      {
         MedianArray[i0] = Output.ArrayImages[i0];
      }

      // Compute the median of the deltas of Output.ArrayImages to its median
      float MedianDelta = GetMAD3x3FLT2(Output.ArrayImages);

      // Compute our median that is the Lorentzian Approximation of MAD
      Output.GVariance = 1.0 / (1.0 + MedianDelta);

      /*
         Construct array of kernels:

         [0] [3] [6]  (Top Row)
         [1] [4] [7]  (Middle Row)
         [2] [5] [8]  (Bottom Row)

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
      Submeans[0] = Output.ArrayImages[0].xy + Output.ArrayImages[1].xy; // Vertical Top-Left (V_TL)
      Submeans[1] = Output.ArrayImages[3].xy + Output.ArrayImages[4].xy; // Vertical Top-Mid (V_TM)
      Submeans[2] = Output.ArrayImages[6].xy + Output.ArrayImages[7].xy; // Vertical Top-Right (V_TR)
      Submeans[3] = Output.ArrayImages[1].xy + Output.ArrayImages[2].xy; // Vertical Bottom-Left (V_BL)
      Submeans[4] = Output.ArrayImages[4].xy + Output.ArrayImages[5].xy; // Vertical Bottom-Mid (V_BM)
      Submeans[5] = Output.ArrayImages[7].xy + Output.ArrayImages[8].xy; // Vertical Bottom-Right (V_BR)
      Submeans[6] = Output.ArrayImages[2].xy + Output.ArrayImages[5].xy; // Horizontal Bottom-Left (H_BL)
      Submeans[7] = Output.ArrayImages[5].xy + Output.ArrayImages[8].xy; // Horizontal Bottom-Right (H_BR)

      Output.SideWindowMeans[0] = Submeans[0] + Submeans[1]; // NW: [0 + 1] + [3 + 4]
      Output.SideWindowMeans[1] = Submeans[1] + Submeans[2]; // NE: [3 + 4] + [6 + 7]
      Output.SideWindowMeans[2] = Submeans[3] + Submeans[4]; // SW: [1 + 2] + [4 + 5]
      Output.SideWindowMeans[3] = Submeans[4] + Submeans[5]; // SE: [4 + 5] + [7 + 8]
      Output.SideWindowMeans[4] = Output.SideWindowMeans[0] + Submeans[2]; // N: [0 + 1 + 3 + 4] + [6 + 7]
      Output.SideWindowMeans[5] = Output.SideWindowMeans[2] + Submeans[5]; // S: [1 + 2 + 4 + 5] + [7 + 8]
      Output.SideWindowMeans[6] = Output.SideWindowMeans[0] + Submeans[6]; // W: [0 + 1 + 3 + 4] + [2 + 5]
      Output.SideWindowMeans[7] = Output.SideWindowMeans[1] + Submeans[7]; // E: [3 + 4 + 6 + 7] + [5 + 8]

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
      const float Epsilon = 1e-7;
      const float3 SpatialDistances = exp2(-float3(0.0, 1.0, 2.0));
      const float VarianceN = 1.0 / (float(Block.Size) - 1.0);

      // Initialize output members
      Block.Sum = 0.0;
      Block.SumWeight = 0.0;

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
               float WeightRange = 1.0 / (DistSqRange + Input.GVariance);

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

      /*
         We initialize by 1 for the following reasons:

         1. Range weighting: Done with Lorentzian approximation

            x / (1 + x)

         2. Compute the inverted variance: Used for variance weighting

            1 / (1 + v)
      */

      float2 VarianceSum = 0.0;

      // Compute the SideWindow's variance
      [unroll]
      for (int i1 = 0; i1 < Input.ArrayImageLength; i1++)
      {
         if (Block.Masks[i1] == 1)
         {
            float2 D = Input.ArrayImages[i1] - Mean;
            VarianceSum += (D * D);
         }
      }

      // Compute the variance weight using a Lorentzian Approximation too
      float Variance = abs(VarianceSum.x) + abs(VarianceSum.y);
      Variance = 1.0 + (Variance * VarianceN);

      // Weight by the local variance
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
