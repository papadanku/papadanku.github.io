
Multilevel Adaptive Side-Window Bilateral Upsampling on the GPU
===============================================================

This document presents an adaptive, multilevel, side-window bilateral upsampling filter designed for motion vectors. The filter incorporates coherence-based range weighting and coherence-weighted side window selection to improve edge preservation and reduce artifacts.

.. seealso::

   Auricchio, G., Giudici, P., & Toscani, G. (2026). How to Measure Multidimensional Variation? Journal of Classification, 43(2), 503–526. https://doi.org/10.1007/s00357-026-09551-8

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

   Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

   Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 8758-8766.

Bilateral Upsampling
--------------------

Bilateral upsampling uses a high-resolution guide image to interpolate a low-resolution target image. Unlike standard linear interpolation, which assumes smoothness across the entire image, bilateral filtering identifies and preserves structural edges.

The filter computes a weighted average of nearby low-resolution pixels. Each pixel's contribution depends on its similarity to the target pixel, as determined by the coherence-based range weighting and covariance-based coherence metric.

Adaptive Weights
----------------

Adaptive bilateral upsampling improves the process by dynamically adjusting the filter's sensitivity based on local image characteristics. Instead of using global constants for the range variance, the algorithm calculates coherence within the filtering window at two different scales: the global window and individual side windows.

In homogeneous regions (high coherence), the filter allows a wider range of pixels to contribute, enhancing smoothing. In edge regions (low coherence), the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures that the filter's strength is proportional to the local content's directional consistency.

The implementation uses a coherence-based approach that computes inverse squared coherence from covariance matrices to determine range weights. This provides more accurate edge preservation than traditional methods.

Global Window: Coherence-based Range Weighting
----------------------------------------------

To determine the overall range sensitivity, the filter calculates the inverse squared coherence from the local image samples using Albert-Zhang's approach. The inverse squared coherence quantifies the relative dispersion of the samples within the window based on the covariance matrix trace and determinant:

The inverse coherence squared is computed as:

.. math::

   \mathrm{InverseCoherence\_Sq} = \frac{4 \cdot \mathrm{det}(\boldsymbol{\Sigma})}{\mathrm{tr}(\boldsymbol{\Sigma})^2}

where :math:`\boldsymbol{\Sigma}` is the covariance matrix of the samples. A high inverse coherence squared indicates greater variability (e.g., near edges), while a low value suggests homogeneity.

This value is computed using the ``GetCovarianceCoherenceInverse_Sq()`` function, which implements the covariance matrix trace and determinant-based coherence calculation for computational efficiency.

Side Windows: Coherence-based Weighting
---------------------------------------

For the "soft-selection" of side windows, the filter calculates the inverse squared coherence for each window using the covariance matrix trace and determinant approach. The inverse coherence squared for each side window is converted to an **Influence Weight** using the following formula:

.. math::

   w_{\mathrm{influence}} = \mathrm{saturate}\left(\mathrm{GetCovarianceCoherenceInverse\_Sq}(\boldsymbol{\mu}_{\mathrm{window}}, \boldsymbol{\Sigma}_{\mathrm{window}})\right)

where :math:`\boldsymbol{\mu}_{\mathrm{window}}` is the mean vector and :math:`\boldsymbol{\Sigma}_{\mathrm{window}}` is the covariance matrix of the samples within the side window.

Unlike traditional methods, this approach uses the inverse coherence squared value directly. **Higher inverse coherence squared (greater variability) results in higher influence weights**. This ensures that windows with less directional consistency (e.g., near edges) contribute more to the final result, improving edge preservation.

Using the Side Window Filter
----------------------------

Conventional filtering algorithms center the local window on the target pixel. When a pixel lies near an edge, this centered window captures samples from both sides of the boundary. Averaging these dissimilar pixels blurs the edge.

The algorithm evaluates multiple side windows, covering cardinal directions and corners. Instead of selecting a single optimal window, it combines their results using a coherence-weighted average. This "soft-selection" approach allows the filter to prioritize windows that align with local edges while still incorporating information from neighboring regions.

The Side Window Filter (SWF) framework supports various filter implementations:

* **Box Filter**: Computes the arithmetic mean of all pixels within the side window.
* **Gaussian Filter**: Applies a weighted average where pixels closer to the target pixel contribute more.
* **Median Filter**: Selects the median value from the window, which effectively removes noise while maintaining edge sharpness.
* **Bilateral Filter**: Weights pixels based on both spatial distance and intensity difference, ensuring only pixels with similar values contribute to the result.

The implemented version follows these steps:

#. **Shared Data Gathering**: A two-pass process that first collects the neighborhood samples and then computes the range weights.
#. **Kernel Generation**: Define a set of kernels representing eight side windows: four cardinal directions and four corners. ASCII diagrams show the window layouts.
#. **Side Window Statistics Calculation**: For each window, compute the local mean :math:`\mu_W` and covariance matrix using precomputed subkernel means for efficiency.
#. **Coherence-Weighted Estimation**: For each window, calculate an influence-weighted mean using the inverse coherence squared value. The inverse coherence squared is computed from the covariance matrix trace and determinant.

#. **Coherence-Weighted Combination**: Combine the estimated means using their coherence-based influence weights (:math:`w_{\mathrm{influence}} = \mathrm{saturate}(\mathrm{GetCovarianceCoherenceInverse\_Sq}(\boldsymbol{\mu}_{\mathrm{window}}, \boldsymbol{\Sigma}_{\mathrm{window}}))`) as weights:

   .. math::

      \mu_{\mathrm{final}} = \frac{\sum \mu_{W_i, \mathrm{bilat}} \cdot w_{\mathrm{influence},i}}{\sum w_{\mathrm{influence},i}}

Karis Averaging for Motion Vectors
----------------------------------

In temporal upsampling, "pulsation" occurs when a filter's selection jumps abruptly between different windows across frames. A standard minimum-variance selection can be highly sensitive to noise, causing these sudden temporal discontinuities.

To mitigate this, we implement a technique inspired by Karis averaging. Instead of brightness-based Karis averaging, this implementation uses **pixel variances** to infer local stability. This ensures smoother temporal upsampling.

The influence weight for each side window (:math:`w_{\mathrm{influence}} = \mathrm{saturate}(\mathrm{GetCovarianceCoherenceInverse\_Sq}(\boldsymbol{\mu}_{\mathrm{window}}, \boldsymbol{\Sigma}_{\mathrm{window}}))`) ensures that the contribution of each side window is proportional to its directional inconsistency. This results in smoother and more coherent upsampled motion vectors.

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

The updated implementation incorporates covariance-based coherence weighting for more accurate edge-aware upsampling.

.. code-block:: hlsl
   :caption: Helper Math Functions (Vector Similarity and Lorentzian)

   float GetCovarianceCoherenceInverse_Sq(float2x2 CoV)
   {
      float Trace = CoV._11 + CoV._22;                                // Tr(J) = a + c
      float Determinant = (CoV._11 * CoV._22) - (CoV._21 * CoV._12);  // Determinant(J) = ac - b^2
      float D = Trace * Trace;

      // If Trace is 0, the neighborhood is completely black/empty, which is isotropic by default.
      float InverseCoherence_Sq = (D > 0.0) ? (4.0 * Determinant) / D : 1.0;
      return InverseCoherence_Sq;
   }

   /*
      Auricchio, G., Giudici, P., & Toscani, G. (2026). How to Measure Multidimensional Variation? Journal of Classification, 43(2), 503–526. https://doi.org/10.1007/s00357-026-09551-8

      Compute the SideWindow's inverse coherence squared from covariance matrix.

      We use the covariance matrix trace and determinant approach based on Auricchio et al. 2026.

      ---

      Covariance matrix structure:

      [xx  xy]
      [xy  yy]
   */

   float GetCoefficientVariation_AZ_InverseSq(
      float2 Mean, float2x2 CovarianceMat)
   {
      // Compute standard quadratic forms: (Mean^T * Covariance) * Mean
      float Numerator = dot(Mean, mul(CovarianceMat, Mean));
      float Denominator = dot(Mean, Mean);

      /*
         Calculate final AZ Coefficient of Variation (Inverse Squared).

            CoV      = sqrt(N) / D
            CoV^2    = N / D^2
            1/CoV^2  = 1 / (N / D^2)
                     = D^2 / N
      */

      float CoV_InverseSq = (Numerator > 0.0) ? (Denominator * Denominator) / Numerator : 1.0;

      return CoV_InverseSq;
   }

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

   struct SharedData_SideWindow_Bilateral
   {
      // Window (Local) information.
      int ArrayImageLength;
      float2 ArrayImages[9];
      float ArrayDistances[9];

      // Side Window Information.
      int SideWindow_Sizes[8];
      float2 SideWindow_Means[8];

      // Shared for final calculation.
      float2 GlobalWindow_Mean;
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

            // Compute the similarity
            Output.ArrayDistances[ImageIndex0] = GetSimilarityJaccard_FLT2(Sample, Output.Reference);

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

      Output.SideWindow_Sizes[0] = SideWindowSize_Corner;
      Output.SideWindow_Sizes[1] = SideWindowSize_Corner;
      Output.SideWindow_Sizes[2] = SideWindowSize_Corner;
      Output.SideWindow_Sizes[3] = SideWindowSize_Corner;
      Output.SideWindow_Sizes[4] = SideWindowSize_Cardinal;
      Output.SideWindow_Sizes[5] = SideWindowSize_Cardinal;
      Output.SideWindow_Sizes[6] = SideWindowSize_Cardinal;
      Output.SideWindow_Sizes[7] = SideWindowSize_Cardinal;

      float2 Subkernel_Means[ArraySideWindowsLength];
      Subkernel_Means[0] = Output.ArrayImages[0] + Output.ArrayImages[1]; // Vertical Top-Left (V_TL)
      Subkernel_Means[1] = Output.ArrayImages[3] + Output.ArrayImages[4]; // Vertical Top-Mid (V_TM)
      Subkernel_Means[2] = Output.ArrayImages[6] + Output.ArrayImages[7]; // Vertical Top-Right (V_TR)
      Subkernel_Means[3] = Output.ArrayImages[1] + Output.ArrayImages[2]; // Vertical Bottom-Left (V_BL)
      Subkernel_Means[4] = Output.ArrayImages[4] + Output.ArrayImages[5]; // Vertical Bottom-Mid (V_BM)
      Subkernel_Means[5] = Output.ArrayImages[7] + Output.ArrayImages[8]; // Vertical Bottom-Right (V_BR)
      Subkernel_Means[6] = Output.ArrayImages[2] + Output.ArrayImages[5]; // Horizontal Bottom-Left (H_BL)
      Subkernel_Means[7] = Output.ArrayImages[5] + Output.ArrayImages[8]; // Horizontal Bottom-Right (H_BR)

      Output.SideWindow_Means[0] = Subkernel_Means[0] + Subkernel_Means[1]; // NW: [0 + 1] + [3 + 4]
      Output.SideWindow_Means[1] = Subkernel_Means[1] + Subkernel_Means[2]; // NE: [3 + 4] + [6 + 7]
      Output.SideWindow_Means[2] = Subkernel_Means[3] + Subkernel_Means[4]; // SW: [1 + 2] + [4 + 5]
      Output.SideWindow_Means[3] = Subkernel_Means[4] + Subkernel_Means[5]; // SE: [4 + 5] + [7 + 8]
      Output.SideWindow_Means[4] = Output.SideWindow_Means[0] + Subkernel_Means[2]; // N: [0 + 1 + 3 + 4] + [6 + 7]
      Output.SideWindow_Means[5] = Output.SideWindow_Means[2] + Subkernel_Means[5]; // S: [1 + 2 + 4 + 5] + [7 + 8]
      Output.SideWindow_Means[6] = Output.SideWindow_Means[0] + Subkernel_Means[6]; // W: [0 + 1 + 3 + 4] + [2 + 5]
      Output.SideWindow_Means[7] = Output.SideWindow_Means[1] + Subkernel_Means[7]; // E: [3 + 4 + 6 + 7] + [5 + 8]
      Output.GlobalWindow_Mean = Output.ArrayImages[0] + Subkernel_Means[3] + Output.SideWindow_Means[7];

      Output.SideWindow_Means[0] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[1] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[2] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[3] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[4] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindow_Means[5] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindow_Means[6] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindow_Means[7] *= SideWindowWeight_Mean_Cardinal;
      Output.GlobalWindow_Mean *= GlobalWeight_Mean;
   }

   void GetSideWindow_Bilateral(
      in int SideWindowIndex,
      in SharedData_SideWindow_Bilateral Input,
      inout SideWindow_Bilateral Block
   )
   {
      // Initialize output members.
      Block.Sum = 0.0;
      Block.SumWeight = 0.0;

      [unroll]
      for (int i0 = 0; i0 < Input.ArrayImageLength; i0++)
      {
         if (Block.Masks[i0] == 1)
         {
            // Accumulate.
            Block.Sum += (Input.ArrayImages[i0] * Input.ArrayDistances[i0]);
            Block.SumWeight += Input.ArrayDistances[i0];
         }
      }

      /*
         Auricchio, G., Giudici, P., & Toscani, G. (2026). How to Measure Multidimensional Variation? Journal of Classification, 43(2), 503–526. https://doi.org/10.1007/s00357-026-09551-8

         Compute the SideWindow's Sample Coefficient of Variance (CoV).

         We use Albert-Zhang's Multivariate Coefficient of Variation because of the computational simplicity.

         ---

         SigmaVec mapping:

         .x = xx (Variance X)
         .y = yy (Variance Y)
         .z = xy (Covariance XY)
      */

      // Constant: Sample Variance (Sigma)
      const float BlockSize = float(Input.SideWindow_Sizes[SideWindowIndex]);
      const float SigmaN = 1.0 / (BlockSize - 1.0);

      float2 Mean = Input.SideWindow_Means[SideWindowIndex];
      float3 SigmaVec = 0.0;

      [unroll]
      for (int i1 = 0; i1 < Input.ArrayImageLength; i1++)
      {
         if (Block.Masks[i1] == 1)
         {
            float2 D = Input.ArrayImages[i1] - Mean;
            SigmaVec += (D.xyx * D.xyy);
         }
      }

      // Normalize to get true sample variance.
      SigmaVec *= SigmaN;

      // Construct the 2x2 Covariance matrix.
      float2x2 CovarianceMat = float2x2(SigmaVec.x, SigmaVec.z, SigmaVec.z, SigmaVec.y);

      // Compute the inverse coherence squared from covariance matrix trace and determinant.
      Block.Influence_Sq = GetCovarianceCoherenceInverse_Sq(CovarianceMat);
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

         What about motion vectors? Instead of measuring the sum of pixel brightness to infer pulsating areas, we use the sum of pixel variances.
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

      WindowMean = (SumInfluence_Sq > 0.0) ? WindowMean / SumInfluence_Sq : SharedData.GlobalWindow_Mean;

      return WindowMean;
   }
