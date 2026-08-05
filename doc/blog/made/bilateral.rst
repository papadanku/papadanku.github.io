
Multilevel Adaptive Side-Window Bilateral Upsampling on the GPU
===============================================================

This document describes an adaptive, multilevel, side-window bilateral upsampling filter for motion vectors. The filter uses coherence-based range weighting and coherence-weighted side window selection to preserve edges and reduce artifacts.

.. seealso::

   Auricchio, G., Giudici, P., & Toscani, G. (2026). How to Measure Multidimensional Variation? *Journal of Classification*, 43(2), 503-526. https://doi.org/10.1007/s00357-026-09551-8

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. *ACM SIGGRAPH 2007 Papers*, 96. https://doi.org/10.1145/1275808.1276497

   Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), *SPIE Proceedings* (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

   Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition* (CVPR), 8758-8766.

Bilateral Upsampling
--------------------

Bilateral upsampling interpolates a low-resolution target image using a high-resolution guide image. Unlike linear interpolation, which assumes uniform smoothness, bilateral filtering preserves structural edges.

The filter computes a weighted average of nearby low-resolution pixels. Each pixel's contribution weight depends on its similarity to the target pixel, determined by coherence-based range weighting and a covariance-based coherence metric.

Adaptive Weights
----------------

Adaptive bilateral upsampling dynamically adjusts filter sensitivity based on local image characteristics. Instead of using global range variance constants, the algorithm calculates coherence at two scales: the global window and individual side windows.

In homogeneous regions with high coherence, the filter allows more pixels to contribute, enhancing smoothing. Near edges with low coherence, the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures filter strength scales with local directional consistency.

The implementation computes inverse squared coherence from covariance matrices to determine range weights. This coherence-based approach preserves edges more accurately than traditional methods.

Global Window: Coherence-based Range Weighting
----------------------------------------------

To determine overall range sensitivity, the filter calculates inverse squared coherence from local image samples. As Auricchio et al. (2026) established, inverse squared coherence quantifies sample dispersion within the window using the covariance matrix trace and determinant:

.. math::

   \mathrm{InverseCoherence\_Sq} = \frac{4 \cdot \mathrm{det}(\boldsymbol{\Sigma})}{\mathrm{tr}(\boldsymbol{\Sigma})^2}

where :math:`\boldsymbol{\Sigma}` is the sample covariance matrix. High inverse coherence squared indicates greater variability near edges; low values indicate homogeneity.

The ``GetCovarianceCoherenceInverse_Sq()`` function computes this value efficiently using the covariance matrix trace and determinant. Due to the Cauchy-Schwarz inequality, the function naturally returns values in the [0,1] range for any 2x2 covariance matrix:

.. math::

   4 \cdot \mathrm{det}(\boldsymbol{\Sigma}) \leq \mathrm{tr}(\boldsymbol{\Sigma})^2

Side Windows: Coherence-based Weighting
---------------------------------------

For soft-selection of side windows, the filter calculates inverse squared coherence for each window using the covariance matrix trace and determinant. Each side window's inverse coherence squared becomes its **Influence Weight**:

.. math::

   w_{\mathrm{influence}} = \mathrm{GetCovarianceCoherenceInverse\_Sq}(\boldsymbol{\mu}_{\mathrm{window}}, \boldsymbol{\Sigma}_{\mathrm{window}})

where :math:`\boldsymbol{\mu}_{\mathrm{window}}` is the mean vector and :math:`\boldsymbol{\Sigma}_{\mathrm{window}}` is the covariance matrix of samples within the side window.

Unlike traditional methods, this approach uses inverse coherence squared directly. **Higher inverse coherence squared yields higher influence weights**, making windows with less directional consistency near edges contribute more. This improves edge preservation.

Using the Side Window Filter
----------------------------

Conventional filters center the local window on the target pixel. Near edges, this centered window captures samples from both boundary sides. Averaging dissimilar pixels blurs the edge.

This algorithm evaluates multiple side windows covering cardinal directions and corners. Instead of selecting one optimal window, it combines results using coherence-weighted averaging. This soft-selection approach prioritizes windows aligned with local edges while incorporating neighboring region information.

The Side Window Filter (SWF) framework supports various filter implementations:

* **Box Filter**: Computes the arithmetic mean of all pixels within the side window.
* **Gaussian Filter**: Applies a weighted average where pixels closer to the target pixel contribute more.
* **Median Filter**: Selects the median value from the window, effectively removing noise while maintaining edge sharpness.
* **Bilateral Filter**: Weights pixels based on both spatial distance and intensity difference, ensuring only similar pixels contribute.

The implemented version follows these steps:

#. **Shared Data Gathering**: A two-pass process that first collects neighborhood samples and then computes range weights.
#. **Kernel Generation**: Define a set of kernels representing eight side windows: four cardinal directions and four corners.

   The sampling grid uses a 3x3 neighborhood with the following layout:

   .. code-block:: text

      0 3 6 [ North West | North  | North East ]
      1 4 7 [    West    | Center |    East    ]
      2 5 8 [ South West | South  | South East ]

   The eight side windows are arranged as follows:

   .. code-block:: text

      NORTH   SOUTH   EAST    WEST
      x x x   - - -   - x x   x x -
      x x x   x x x   - x x   x x -
      - - -   x x x   - x x   x x -

      NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
      x x -       - x x       - - -       - - -
      x x -       - x x       x x -       - x x
      - - -       - - -       x x -       - x x

#. **Side Window Statistics Calculation**: For each window, compute the local mean :math:`\\mu_W` and covariance matrix using precomputed subkernel means for efficiency.
#. **Coherence-Weighted Estimation**: For each window, calculate an influence-weighted mean using the inverse coherence squared value.
#. **Coherence-Weighted Combination**: Combine the estimated means using their coherence-based influence weights as weights:

   .. math::

      \mu_{\mathrm{final}} = \frac{\sum \mu_{W_i, \mathrm{bilat}} \cdot w_{\mathrm{influence},i}}{\sum w_{\mathrm{influence},i}}

Karis Averaging for Motion Vectors
----------------------------------

In temporal upsampling, pulsation occurs when filter selection jumps abruptly between windows across frames. Standard minimum-variance selection, being noise-sensitive, causes sudden temporal discontinuities.

To mitigate pulsation, we implement variance-weighted averaging inspired by CBloom's Karis averaging. While traditional Karis averaging uses brightness to detect pulsating areas, our adaptation uses pixel variances to infer local stability. Each side window's contribution is weighted by its variance: windows with higher variance (less directional consistency) contribute more. This prevents pulsating regions during temporal upsampling by ensuring smooth frame transitions.

The influence weight :math:`w_{\mathrm{influence}} = \mathrm{GetCovarianceCoherenceInverse\_Sq}(\boldsymbol{\mu}_{\mathrm{window}}, \boldsymbol{\Sigma}_{\mathrm{window}})` ensures each side window's contribution scales with its directional inconsistency, producing smoother, more coherent upsampled motion vectors.

Using Image Pyramids
--------------------

A multilevel scheme employs an image pyramid for recursive upsampling. Instead of a single-step operation, the algorithm increases resolution incrementally (e.g., in :math:`2 \times 2` stages).

At each pyramid level, the adaptive side-window bilateral filter is applied to the current resolution. This recursive refinement minimizes aliasing artifacts and reduces computational cost compared to single-step high-resolution filtering.

Multilevel Adaptive Side-Window Bilateral Upsampling
----------------------------------------------------

The proposed technique integrates the following components:

* **Adaptive Weighting**: Dynamically adjusts range parameters based on local image coherence.
* **Side Window Filtering**: Evaluates multiple shifted windows to identify the one best aligned with the target pixel.
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
         1 1 1   0 0 0   0 1 1   1 1 0
         1 1 1   1 1 1   0 1 1   1 1 0
         0 0 0   1 1 1   0 1 1   1 1 0

         NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
         1 1 0       0 1 1       0 0 0       0 0 0
         1 1 0       0 1 1       1 1 0       0 1 1
         0 0 0       0 0 0       1 1 0       0 1 1
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
         Auricchio, G., Giudici, P., & Toscani, G. (2026). How to Measure Multidimensional Variation? Journal of Classification, 43(2), 503-526. https://doi.org/10.1007/s00357-026-09551-8

         Compute the SideWindow's Sample Coefficient of Variance (CoV).

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
         1 1 1   0 0 0   0 1 1   1 1 0
         1 1 1   1 1 1   0 1 1   1 1 0
         0 0 0   1 1 1   0 1 1   1 1 0

         NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
         1 1 0       0 1 1       0 0 0       0 0 0
         1 1 0       0 1 1       1 1 0       0 1 1
         0 0 0       0 0 0       1 1 0       0 1 1
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
