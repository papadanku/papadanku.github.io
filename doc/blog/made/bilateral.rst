
Multilevel Adaptive Side-Window Bilateral Upsampling on the GPU
===============================================================

This document proposes an adaptive, multilevel, side-window bilateral upsampling filter designed for motion vectors, incorporating coherence-based range weighting and coherence-weighted side window selection.

.. seealso::

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

   Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

   Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 8758-8766.

Bilateral Upsampling
--------------------

Bilateral upsampling uses a high-resolution guide image to interpolate a low-resolution target image. Unlike standard linear interpolation, which assumes a smoothness prior, this technique uses the guide image to identify structural edges.

The filter computes a weighted average of nearby low-resolution pixels. The weight for each pixel depends on two factors:

* **Spatial Distance**: Pixels closer to the target location contribute more.
* **Intensity Difference**: Pixels in the guide image with similar intensities to the target guide pixel contribute more.

This dual-weighting ensures that only pixels on the same side of an edge contribute to the result, effectively preserving structural boundaries.

Adaptive Weights
----------------

Adaptive bilateral upsampling improves the process by dynamically adjusting the filter's sensitivity based on local image characteristics. Instead of using global constants for the range variance, the algorithm calculates coherence within the filtering window at two different scales: the global window and individual side windows.

In homogeneous regions (high coherence), the filter allows a wider range of pixels to contribute, enhancing smoothing. In edge regions (low coherence), the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures that the filter's strength is proportional to the local content's directional consistency.

The implementation uses a coherence-based approach that computes normalized squared coherence from covariance matrices to determine range weights, providing more accurate edge preservation than traditional methods.

Global Window: Coherence-based Range Weighting
----------------------------------------------

To determine the overall range sensitivity, the filter calculates a normalized squared coherence based on the covariance of local image samples. This coherence value, which ranges from 0 to 1, quantifies the directional consistency of the samples within the window. A high coherence indicates a strong, well-defined edge, whereas a low coherence suggests a more isotropic or homogeneous region.

The coherence :math:`C` is computed using the covariance matrix of the samples and is defined as:

.. math::

   C = \frac{4 \cdot \left[ \left( \frac{\|\mathbf{G}_x\|^2 - \|\mathbf{G}_y\|^2}{2} \right)^2 + (\mathbf{G}_x \cdot \mathbf{G}_y)^2 \right]}{(\|\mathbf{G}_x\|^2 + \|\mathbf{G}_y\|^2)^2}

The global coherence calculation in the implementation uses this formula to compute a coherence value, which is then converted to a weight using:

.. math::

   w_{global} = 1.0 - \text{saturate}(C)

For range weighting, the implementation uses a simple inverse squared distance metric:

.. math::

   w_r = \frac{1}{\max(1, \|\Delta \text{Range}\|^2)}

Side Windows: Coherence-based Weighting
---------------------------------------

For the "soft-selection" of side windows, the filter calculates coherence for each window using the same covariance-based approach as the global window. This allows the algorithm to weight windows based on their local directional consistency.

The coherence for each side window is computed using the covariance matrix of the samples within that window, with the same formula as the global coherence. The implementation then converts this coherence value to an influence weight using:

.. math::

   w_{influence} = 1.0 - \text{saturate}(C_{window})

Higher coherence values (closer to 1) indicate more directionally consistent regions, which receive higher influence weights in the final combination.

Using the Side Window Filter
----------------------------

Conventional filtering algorithms center the local window on the target pixel. When a pixel lies near an edge, this centered window captures samples from both sides of the boundary. Averaging these dissimilar pixels blurs the edge.

The algorithm evaluates multiple side windows, covering cardinal directions and corners. Instead of selecting a single optimal window, it combines their results using a coherence-weighted average. This "soft-selection" approach allows the filter to prioritize windows that align with local edges while still incorporating information from neighboring regions.

The SWF framework supports various filter implementations:

* **Box Filter**: Computes the arithmetic mean of all pixels within the side window.
* **Gaussian Filter**: Applies a weighted average where pixels closer to the target pixel contribute more.
* **Median Filter**: Selects the median value from the window, which effectively removes noise while maintaining edge sharpness.
* **Bilateral Filter**: Weights pixels based on both spatial distance and intensity difference, ensuring only pixels with similar values contribute to the result.

The implemented version follows these steps:

#. **Shared Data Gathering**: A two-pass process that first collects the neighborhood samples and then computes the range weights using the inverse squared distance metric: :math:`w_r = \frac{1}{\max(1, \|\Delta \text{Range}\|^2)}`.
#. **Kernel Generation**: Define a set of kernels representing eight side windows: four cardinal directions and four corners, with ASCII diagrams showing the window layouts.
#. **Side Window Statistics Calculation**: For each window, compute the local mean :math:`\mu_W` and covariance matrix using precomputed subkernel means for efficiency.
#. **Bilateral Weighted Estimation**: For each window, calculate a bilateral-weighted mean :math:`\mu_{W, \text{bilat}}`. The range weight uses the simple inverse squared distance metric.
#. **Coherence-Weighted Combination**: Combine the estimated means using their coherence-based influence weights (:math:`w_{influence} = 1.0 - \text{saturate}(C_{window})`) as weights:

   .. math::

      \mu_{\text{final}} = \frac{\sum \mu_{W_i, \text{bilat}} \cdot w_{influence,i}}{\sum w_{influence,i}}

Karis Averaging for Motion Vectors
----------------------------------

In temporal upsampling, "pulsation" occurs when a filter's selection jumps abruptly between different windows across frames. A standard minimum-variance selection can be highly sensitive to noise, causing these sudden temporal discontinuities.

To mitigate this, we implement a technique inspired by Karis averaging. While standard Karis averaging uses pixel brightness to prevent over-brightening, this implementation uses coherence-based weights to infer local stability. The influence weight for each side window (:math:`w_{influence} = 1.0 - \text{saturate}(C_{window})`) ensures that the contribution of each side window is proportional to its directional consistency, resulting in smoother and more coherent upsampled motion vectors.

Using Image Pyramids
--------------------

A multilevel scheme employs an image pyramid for recursive upsampling. Instead of a single-step upsampling operation, the algorithm increases resolution incrementally (e.g., in :math:`2 \times 2` stages).

At each pyramid level, the adaptive side-window bilateral filter is applied to the current resolution. This recursive refinement minimizes aliasing artifacts and reduces the overall computational cost compared to a single-step high-resolution filter.

Multilevel Adaptive Side-Window Bilateral Upsampling
----------------------------------------------------

The proposed technique integrates the following components:

* **Adaptive Weighting**: Dynamically adjusts the filter's range parameters based on local image coherence.
* **Side Window Filtering**: Evaluates multiple shifted windows to identify the one that best aligns with the target pixel.
* **Image Pyramids**: Employs recursive upsampling to optimize computational efficiency.

.. code-block:: hlsl
   :caption: Helper Math Functions

   /*
      Compute the Coherance.

      Simplication of the factor inside the square root (S):

         1. Tr(M)^2 - 4det(M)
         2. (a + c)^2 - 4(ac - b^2)
         3. a^2 + 2ac + c^2 - 4ac + 4b^2
         4. a^2 - 2ac + c^2 + 4b^2
         5. (a - c)^2 + 4b^2

         1. E = (Tr(M) +- sqrt((a - c)^2 + 4b^2)) / 2
         2. E = (Tr(M) / 2) +- sqrt(((a - c)^2 / 4) + (4b^2 / 4))
         3. E = (Tr(M) / 2) +- sqrt(((a - c) / 2)^2 + b^2)

         E1 = (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2)
         E2 = (Tr(M) / 2) - sqrt(((a - c) / 2)^2 + b^2)

      Now we need to compute C: (E1 - E2) / (E1 + E2)

         E1 - E2:

            1. ((Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2)) - ((Tr(M) / 2) - sqrt(((a - c) / 2)^2 + b^2))
            2. (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2) - (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2)
            3. sqrt(((a - c) / 2)^2 + b^2) + sqrt(((a - c) / 2)^2 + b^2)
            4. 2 * sqrt(((a - c) / 2)^2 + b^2)

         E1 + E2:

            1. (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2) + ((Tr(M) / 2) - sqrt(((a - c) / 2)^2 + b^2))
            2. (Tr(M) / 2) + (Tr(M) / 2)
            3. 2 * (Tr(M) / 2)
            4. Tr(M)

         Therefore: (2 * sqrt(((a - c) / 2)^2 + b^2)) / Tr(M)
   */

   float GetCovarianceCoherence_Sq(
      float3 CovarianceVec // .x = xx; .y = yy; .z = .xy or yx
   )
   {
      float GxGx = CovarianceVec[0];
      float GyGy = CovarianceVec[1];
      float GxGy = CovarianceVec[2];

      float Trace = (GxGx + GyGy);          // Element (a + c)
      float Diff  = (GxGx - GyGy) * 0.5;    // Element (a - c) / 2
      float N = (Diff * Diff) + (GxGy * GxGy);
      float D = Trace * Trace;

      // Normalized Squared Coherence: 0 (flat), 1 (highly directional edge)
      float Coherence_Sq = (D > 0.0) ? (4.0 * N) / D : 0.0;

      return Coherence_Sq;
   }

.. code-block:: hlsl
   :caption: Variance-Weighted Adaptive, Multilevel, Side-Window Bilateral Upsampling

   /*
      This is an optimized, self-guided version for Joint Bilateral Upsampling implemented in HLSL.

      The implementation features:
      - Adaptive coherence-based range weighting
      - Eight side windows with spatial masks
      - Coherence-weighted combination
      - Karis averaging-inspired temporal stability

      Inspired by:
      - Kopf et al. (2007) - Joint bilateral upsampling
      - Riemens et al. (2009) - Multistep joint bilateral depth upsampling
      - Yin et al. (2019) - Side window filtering

      References:
         Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

         Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

         Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 8758-8766.
   */

   struct SharedData_SideWindow_Bilateral
   {
      // Window (Local) information.
      int ArrayImageLength;
      float2 ArrayImages[9];
      float ArrayDistancesRange[9];
      float ArrayDistancesSpatial[9];

      // Window (Global) information.
      float2 GlobalWindowMean;
      float GlobalWindowCoherence_Sq;

      // Side Window Information.
      int SideWindowSizes[8];
      float2 SideWindowMeans[8];

      // Shared for final calculation.
      float2 Reference;
   };

   struct SideWindow_Bilateral
   {
      int Masks[9];

      float2 Sum;
      float SumWeight;
      float Influence_Sq;
   };

   void GetSharedData_SideWindow_Bilateral(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex,
      out SharedData_SideWindow_Bilateral Output
   )
   {
      const int ArrayImageLength = 9;
      const int ArraySideWindowsLength = 8;

      // Initialize variables
      Output.ArrayImageLength = ArrayImageLength;
      Output.Reference = tex2D(Guide, Tex).xy;

      // Compute an array Covariance Sums to calculate Side Window Coherence
      float3 CovarianceElement[9];
      float3 SideWindowCovarianceMatrix[8];
      float3 GlobalWindowCovarianceMatrix;

      // Precompute (static)
      float2 PixelSize = fwidth(Tex.xy);

      /*
         Gather samples:

         0 3 6 [ North West | North  | North East ]
         1 4 7 [    West    | Center |    East    ]
         2 5 8 [ South West | South  | South East ]
      */

      // Initialize counter here
      int ImageIndex0 = 0;

      [unroll]
      for (int x0 = -1; x0 <= 1; x0++)
      {
         [unroll]
         for (int y0 = -1; y0 <= 1; y0++)
         {
            // *2 because the lower sample takes a 2 texel footprint.
            float2 Delta = float2(x0, y0) * 2.0;
            float2 Offset = Tex + (Delta * PixelSize);
            float2 Sample = tex2D(Image, Offset).xy;

            // This is for our Side Window calculation.
            Output.ArrayImages[ImageIndex0] = Sample;

            // This is for our Side Window Coherence calculation.
            CovarianceElement[ImageIndex0] = Sample.xyx * Sample.xyy;

            ImageIndex0 += 1;
         }
      }

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

      const int SideWindowSize_Corner = 4;
      const int SideWindowSize_Cardinal = 6;

      const float SideWindowWeight_Mean_Corner = 1.0 / float(SideWindowSize_Corner);
      const float SideWindowWeight_Mean_Cardinal = 1.0 / float(SideWindowSize_Cardinal);
      const float GlobalWeight_Mean = 1.0 / float(ArrayImageLength);

      Output.SideWindowSizes[0] = SideWindowSize_Corner;
      Output.SideWindowSizes[1] = SideWindowSize_Corner;
      Output.SideWindowSizes[2] = SideWindowSize_Corner;
      Output.SideWindowSizes[3] = SideWindowSize_Corner;
      Output.SideWindowSizes[4] = SideWindowSize_Cardinal;
      Output.SideWindowSizes[5] = SideWindowSize_Cardinal;
      Output.SideWindowSizes[6] = SideWindowSize_Cardinal;
      Output.SideWindowSizes[7] = SideWindowSize_Cardinal;

      float2 Subkernel_Means[8];
      Subkernel_Means[0] = Output.ArrayImages[0] + Output.ArrayImages[1]; // Vertical Top-Left (V_TL)
      Subkernel_Means[1] = Output.ArrayImages[3] + Output.ArrayImages[4]; // Vertical Top-Mid (V_TM)
      Subkernel_Means[2] = Output.ArrayImages[6] + Output.ArrayImages[7]; // Vertical Top-Right (V_TR)
      Subkernel_Means[3] = Output.ArrayImages[1] + Output.ArrayImages[2]; // Vertical Bottom-Left (V_BL)
      Subkernel_Means[4] = Output.ArrayImages[4] + Output.ArrayImages[5]; // Vertical Bottom-Mid (V_BM)
      Subkernel_Means[5] = Output.ArrayImages[7] + Output.ArrayImages[8]; // Vertical Bottom-Right (V_BR)
      Subkernel_Means[6] = Output.ArrayImages[2] + Output.ArrayImages[5]; // Horizontal Bottom-Left (H_BL)
      Subkernel_Means[7] = Output.ArrayImages[5] + Output.ArrayImages[8]; // Horizontal Bottom-Right (H_BR)

      Output.SideWindowMeans[0] = Subkernel_Means[0] + Subkernel_Means[1]; // NW: [0 + 1] + [3 + 4]
      Output.SideWindowMeans[1] = Subkernel_Means[1] + Subkernel_Means[2]; // NE: [3 + 4] + [6 + 7]
      Output.SideWindowMeans[2] = Subkernel_Means[3] + Subkernel_Means[4]; // SW: [1 + 2] + [4 + 5]
      Output.SideWindowMeans[3] = Subkernel_Means[4] + Subkernel_Means[5]; // SE: [4 + 5] + [7 + 8]
      Output.SideWindowMeans[4] = Output.SideWindowMeans[0] + Subkernel_Means[2]; // N: [0 + 1 + 3 + 4] + [6 + 7]
      Output.SideWindowMeans[5] = Output.SideWindowMeans[2] + Subkernel_Means[5]; // S: [1 + 2 + 4 + 5] + [7 + 8]
      Output.SideWindowMeans[6] = Output.SideWindowMeans[0] + Subkernel_Means[6]; // W: [0 + 1 + 3 + 4] + [2 + 5]
      Output.SideWindowMeans[7] = Output.SideWindowMeans[1] + Subkernel_Means[7]; // E: [3 + 4 + 6 + 7] + [5 + 8]
      Output.GlobalWindowMean = Output.ArrayImages[0] + Subkernel_Means[3] + Output.SideWindowMeans[7];

      Output.SideWindowMeans[0] *= SideWindowWeight_Mean_Corner;
      Output.SideWindowMeans[1] *= SideWindowWeight_Mean_Corner;
      Output.SideWindowMeans[2] *= SideWindowWeight_Mean_Corner;
      Output.SideWindowMeans[3] *= SideWindowWeight_Mean_Corner;
      Output.SideWindowMeans[4] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindowMeans[5] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindowMeans[6] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindowMeans[7] *= SideWindowWeight_Mean_Cardinal;
      Output.GlobalWindowMean *= GlobalWeight_Mean;

      /*
         Compute the Coherence for every side window.

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

      const float GlobalWindowSize_Coherence = 1.0 / (float(ArrayImageLength) - 1.0);

      /*
         | xx xy |
         | yx yy |

         .x = x^2 - (x_mean * x_mean)
         .y = y^2 - (y_mean * y_mean)
         .z = x*y - (x_mean * y_mean)
      */

      float3 CovarianceVec = 0.0;

      [unroll]
      for (int i0 = 0; i0 < ArrayImageLength; i0++)
      {
         float2 D = Output.ArrayImages[i0] - Output.GlobalWindowMean;
         CovarianceVec += (D.xyx * D.xyy);
      }

      // Normalize to Sample Variance
      CovarianceVec *= GlobalWindowSize_Coherence;
      Output.GlobalWindowCoherence_Sq = 1.0 - saturate(GetCovarianceCoherence_Sq(CovarianceVec));

      // Reset counter and start again
      int ImageIndex1 = 0;

      [unroll]
      for (int x1 = -1; x1 <= 1; x1++)
      {
         [unroll]
         for (int y1 = -1; y1 <= 1; y1++)
         {
            // Compute shared Weight (Range) here.
            float2 DeltaRange = Output.ArrayImages[ImageIndex1] - Output.Reference;
            Output.ArrayDistancesRange[ImageIndex1] = 1.0 / max(1.0, dot(DeltaRange, DeltaRange));
            Output.ArrayDistancesSpatial[ImageIndex1] = exp2(-(abs(x1) + abs(y1)));

            ImageIndex1 += 1;
         }
      }
   }

   void GetSideWindow_Bilateral(
      in int SideWindowIndex,
      in SharedData_SideWindow_Bilateral Input,
      inout SideWindow_Bilateral Block
   )
   {
      // Pre-compute Spatial distances.
      // .x = Center (0 + 0); .y = Diagonal (1 + 1); .z = Cardinal (0 + 1)
      const float Epsilon = 1e-7;
      const float3 SpatialDistances = exp2(-float3(0.0, 1.0, 2.0));

      // Initialize output members.
      Block.Sum = 0.0;
      Block.SumWeight = 0.0;

      [unroll]
      for (int i0 = 0; i0 < Input.ArrayImageLength; i0++)
      {
         if (Block.Masks[i0] == 1)
         {
            // Fetch Weights and combine.
            float WeightSpatial = Input.ArrayDistancesSpatial[i0];
            float WeightRange = Input.ArrayDistancesRange[i0];
            float Weight = WeightSpatial * WeightRange;

            // Accumulate.
            Block.Sum += (Input.ArrayImages[i0] * Weight);
            Block.SumWeight += Weight;
         }
      }

      /*
         .x = x^2 - (x_mean * x_mean)
         .y = y^2 - (y_mean * y_mean)
         .z = x*y - (x_mean * y_mean)
      */

      float CovarianceN = 1.0 / (float(Input.SideWindowSizes[SideWindowIndex]) - 1.0);
      float3 CovarianceVec = 0.0;

      [unroll]
      for (int i1 = 0; i1 < Input.ArrayImageLength; i1++)
      {
         if (Block.Masks[i1] == 1)
         {
            float2 D = Input.ArrayImages[i1] - Input.SideWindowMeans[SideWindowIndex];
            CovarianceVec += (D.xyx * D.xyy);
         }
      }

      // Normalize to Sample Variance
      CovarianceVec *= CovarianceN;
      Block.Influence_Sq = 1.0 - saturate(GetCovarianceCoherence_Sq(CovarianceVec));
   }

   float2 GetSelfBilateralUpsample_FLT2(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex
   )
   {
      const int SideWindowsCount = 8;

      // Create the data struct that we will use accross multiple functions.
      SharedData_SideWindow_Bilateral SharedData;
      GetSharedData_SideWindow_Bilateral(Image, Guide, Tex, SharedData);

      /*
         Construct array of Masks:

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

      // Initialize our side windows
      SideWindow_Bilateral SideWindows[SideWindowsCount];
      SideWindows[0].Masks = { 1, 1, 0, 1, 1, 0, 0, 0, 0 }; // NW
      SideWindows[1].Masks = { 0, 0, 0, 1, 1, 0, 1, 1, 0 }; // NE
      SideWindows[2].Masks = { 0, 1, 1, 0, 1, 1, 0, 0, 0 }; // SW
      SideWindows[3].Masks = { 0, 0, 0, 0, 1, 1, 0, 1, 1 }; // SE
      SideWindows[4].Masks = { 1, 1, 0, 1, 1, 0, 1, 1, 0 }; // N
      SideWindows[5].Masks = { 0, 1, 1, 0, 1, 1, 0, 1, 1 }; // S
      SideWindows[6].Masks = { 1, 1, 1, 1, 1, 1, 0, 0, 0 }; // W
      SideWindows[7].Masks = { 0, 0, 0, 1, 1, 1, 1, 1, 1 }; // E

      /*
         Calculate the variance-weighted Side Window filter. This may sound strange, but it works better than the regular min(x) method.

         While Google's enterprise-class clanker suggested this method, I did my discernment and revised it to work like do CBloom's Karis averaging. In layman's terms, a Karis average means "we will add 4 things together: darken the very-bright things and keep the not-very-bright-things the same". The "thing" is either a single pixel (for a Full Karis Average) or a sum of pixels (for a Partial Karis Average). We use the Karis average to prevent pulsating regions when downsampling.

         What about motion vectors? Instead of measuring the sum of pixel brightness to infer pulsating areas, we use coherence-based weights.
      */

      float2 WindowMean = 0.0;
      float SumInfluence_Sq = 0.0;

      [unroll]
      for (int i0 = 0; i0 < SideWindowsCount; i0++)
      {
         GetSideWindow_Bilateral(i0, SharedData, SideWindows[i0]);
         if (SideWindows[i0].SumWeight > 0.0)
         {
            // Normalize the sum.
            float2 Sum = SideWindows[i0].Sum / SideWindows[i0].SumWeight;

            // Weighted sum by influence.
            WindowMean += (Sum * SideWindows[i0].Influence_Sq);
            SumInfluence_Sq += SideWindows[i0].Influence_Sq;
         }
      }

      WindowMean = (SumInfluence_Sq > 0.0) ? WindowMean / SumInfluence_Sq : SharedData.GlobalWindowMean;

      return WindowMean;
   }
