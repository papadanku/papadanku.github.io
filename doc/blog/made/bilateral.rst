
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

Bilateral upsampling interpolates a low-resolution target image using a high-resolution guide image. Unlike linear interpolation, which assumes uniform smoothness, bilateral filtering preserves structural edges by weighting pixel contributions based on both spatial proximity and intensity similarity.

The filter computes a weighted average of nearby low-resolution pixels. Each pixel's contribution weight depends on its similarity to the target pixel, determined by coherence-based range weighting and a covariance-based coherence metric that adapts to local image structure.

Adaptive Weights
----------------

In homogeneous regions with high coherence, the filter allows more pixels to contribute, enhancing smoothing. Near edges with low coherence, the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures filter strength scales with local directional consistency.

The implementation computes inverse coherence from covariance matrices to determine range weights. This coherence-based approach preserves edges more accurately than traditional methods by dynamically adjusting filter parameters based on local image structure.

Global Window: Coherence-based Range Weighting
----------------------------------------------

Bilateral upsampling requires determining how much each neighboring pixel should contribute to the target pixel. Unlike traditional methods that use fixed spatial or intensity distances, our approach uses **coherence-based range weighting** that adapts to local image structure.

The coherence metric quantifies the dispersion of samples within a window using the sample covariance matrix :math:`\boldsymbol{\Sigma}`, which for 2D vectors is:

.. math::

   \boldsymbol{\Sigma} = \begin{bmatrix}
   \sigma_{xx} & \sigma_{xy} \\
   \sigma_{xy} & \sigma_{yy}
   \end{bmatrix}

where:

* :math:`\sigma_{xx}` and :math:`\sigma_{yy}` are the variances along each dimension
* :math:`\sigma_{xy}` is the covariance between dimensions

The inverse coherence provides a normalized measure of homogeneity:

.. math::

   \mathrm{InverseCoherence}(\boldsymbol{\Sigma}) = 1 - \frac{\lambda_{1} - \lambda_{2}}{\lambda_{1} + \lambda_{2}} = \frac{2\lambda_{2}}{\lambda_{1} + \lambda_{2}}
   \\
   \\
   \text{where } \lambda_{1}, \lambda_{2} \text{ are the eigenvalues of } \boldsymbol{\Sigma}

This formulation ensures :math:`0 < \mathrm{InverseCoherence}(\boldsymbol{\Sigma}) \leq 1`, where:

* **1** indicates perfect isotropy (no directional bias, homogeneous region)
* **Values approaching 0** indicate strong directional structure (edges)

.. admonition:: Mathematical Significance

   The inverse coherence metric quantifies sample dispersion within a window. Due to the Cauchy-Schwarz inequality, this metric naturally satisfies :math:`0 < \mathrm{InverseCoherence}(\boldsymbol{\Sigma}) \leq 1` for any valid covariance matrix:

   .. math::

      \mathrm{tr}(\boldsymbol{\Sigma})^2 \geq 4 \cdot \mathrm{det}(\boldsymbol{\Sigma})

   The ``GetCovarianceCoherence_Inverse()`` function computes this value efficiently using the closed-form solution for 2x2 covariance matrices, making it suitable for real-time GPU implementation.

Side Windows: Coherence-based Weighting
---------------------------------------

Conventional bilateral filters use a single centered window, which captures pixels from both sides of edges, causing blurring. Our approach instead uses **eight shifted side windows** covering all cardinal directions and corners.

Each side window :math:`W_i` (where :math:`i \in \{1, 2, ..., 8\}`) has its own coherence metric computed from the samples within that window. The **influence weight** for each window is:

.. math::

   w_{\mathrm{influence},i} = \mathrm{GetCovarianceCoherence\_Inverse}( \boldsymbol{\mu}_{W_i}, \boldsymbol{\Sigma}_{W_i} )

Unlike traditional hard-selection approaches that choose a single optimal window, we use **soft-selection** where all windows contribute to the final result, weighted by their coherence. This approach:

* **Preserves edges** by emphasizing windows aligned with local structure
* **Reduces artifacts** by incorporating information from neighboring regions
* **Improves robustness** to noise through adaptive weighting

The :math:`\mathrm{GetCovarianceCoherence\_Inverse}()` function efficiently computes this metric using the closed-form solution for 2x2 covariance matrices, making it suitable for real-time GPU implementation.

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
      :caption: 3x3 Sampling Grid

      0 3 6 [ North West | North  | North East ]
      1 4 7 [    West    | Center |    East    ]
      2 5 8 [ South West | South  | South East ]

   The eight side windows are arranged as follows:

   .. code-block:: text
      :caption: Side Window Masks

      NORTH   SOUTH   EAST    WEST
      x x x   - - -   - x x   x x -
      x x x   x x x   - x x   x x -
      - - -   x x x   - x x   x x -

      NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
      x x -       - x x       - - -       - - -
      x x -       - x x       x x -       - x x
      - - -       - - -       x x -       - x x

#. **Side Window Statistics Calculation**: For each window :math:`W_i`, compute the local mean :math:`\boldsymbol{\mu}_{W_i}` and covariance matrix :math:`\boldsymbol{\Sigma}_{W_i}` using precomputed subkernel means for efficiency.
#. **Coherence-Weighted Estimation**: For each window :math:`W_i`, calculate an influence-weighted mean:

   .. math::

      \mu_{W_i}^{\mathrm{bilat}} = \frac{\sum_{j \in W_i} \mathbf{p}_j \cdot w_{\mathrm{similarity}}(j)}{\sum_{j \in W_i} w_{\mathrm{similarity}}(j)}

   where :math:`w_{\mathrm{similarity}}(j)` is the similarity weight between pixel :math:`j` and the guide image.

#. **Coherence-Weighted Combination**: Combine the estimated means using their coherence-based influence weights as weights:

   .. math::

      \mu_{\mathrm{final}} = \frac{\sum_{i=1}^{8} \mu_{W_i}^{\mathrm{bilat}} \cdot w_{\mathrm{influence},i}}{\sum_{i=1}^{8} w_{\mathrm{influence},i}}

   This final combination produces a result that is both edge-aware and robust to noise.

.. admonition:: Normalized Weighted Average

   The final result is computed as a weighted average where each side window's bilateral-filtered mean :math:`\mu_{W_i}^{\mathrm{bilat}}` is multiplied by its influence weight :math:`w_{\mathrm{influence},i}`. The normalization ensures the result remains unbiased regardless of the number of contributing windows.

Karis Averaging for Temporal Stability
--------------------------------------

In temporal upsampling, **pulsation artifacts** occur when filter selection jumps abruptly between windows across consecutive frames. Standard minimum-variance selection methods are particularly susceptible to noise, causing sudden temporal discontinuities that manifest as flickering in the output.

To mitigate pulsation, we implement **variance-weighted averaging** inspired by CBloom's Karis averaging technique. While traditional Karis averaging uses pixel brightness to detect pulsating areas, our adaptation uses **pixel variances** to infer local stability:

.. math::

   w_{\mathrm{influence},i} = \mathrm{GetCovarianceCoherence\_Inverse}( \boldsymbol{\mu}_{W_i}, \boldsymbol{\Sigma}_{W_i} )

The key insight is that windows with higher variance (indicating less directional consistency) should contribute more to the final result. This variance-weighting strategy:

* **Prevents pulsating regions** by ensuring smooth transitions between frames
* **Maintains temporal coherence** in upsampled motion vectors
* **Adapts to local structure** through the coherence metric

.. admonition:: Karis Averaging Adaptation

   Traditional Karis averaging uses brightness values to detect pulsating areas. Our adaptation replaces brightness with variance: windows with higher variance (less directional consistency) contribute more to the final result. This prevents abrupt transitions between frames, ensuring temporal coherence in motion vector upsampling.

Using Image Pyramids
--------------------

A **multilevel scheme** employing an image pyramid enables recursive upsampling that progressively increases resolution. Instead of performing a single high-resolution filtering operation, the algorithm increases resolution incrementally in :math:`2 \times 2` stages.

At each pyramid level :math:`L`, the adaptive side-window bilateral filter is applied to the current resolution. This recursive refinement offers several advantages:

* **Minimizes aliasing artifacts** through progressive refinement
* **Reduces computational cost** compared to single-step high-resolution filtering
* **Improves convergence** by starting from a coarser approximation

The multilevel approach is particularly effective for motion vector upsampling, where temporal coherence across scales is crucial for maintaining visual quality.

Multilevel Adaptive Side-Window Bilateral Upsampling
----------------------------------------------------

The proposed technique integrates three key innovations to achieve high-quality edge-aware upsampling:

.. admonition:: Core Components

   Adaptive Weighting
      Dynamically adjusts range parameters based on local image coherence using the inverse coherence metric :math:`InverseCoherence`. This adaptation preserves edges while smoothing homogeneous regions.

   Side Window Filtering
      Evaluates multiple shifted windows (cardinal directions and corners) to identify the one best aligned with the target pixel's local structure. The soft-selection approach combines all windows weighted by their coherence :math:`InverseCoherence`.

   Image Pyramids
      Employs recursive upsampling through a multilevel pyramid scheme, progressively increasing resolution while maintaining temporal coherence across scales.

The updated implementation incorporates covariance-based coherence weighting for more accurate edge-aware upsampling, making it particularly suitable for motion vector refinement in real-time applications.

.. code-block:: hlsl
   :caption: Helper Math Functions (Vector Similarity and Lorentzian)

   float GetCovarianceCoherence_Inverse(float2x2 CoV)
   {
      float Tr = CoV._11 + CoV._22;   // Element (a + c)
      float Df = CoV._11 - CoV._22;   // Element (a - c)
      float N = Tr - sqrt((Df * Df) + (4.0 * (CoV._12 * CoV._12)));

      // Normalized Isotropy: 0 (highly directional edge), 1 (flat)
      float InverseCoherence = (abs(Tr) > 0.0) ? N / Tr : 1.0;
      return InverseCoherence;
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
      float2 Reference;
   };

   struct SideWindow_Bilateral
   {
      int Masks[9];

      float2 Sum;
      float SumWeight;
      float Influence;
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

      Output.SideWindow_Means[0] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[1] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[2] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[3] *= SideWindowWeight_Mean_Corner;
      Output.SideWindow_Means[4] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindow_Means[5] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindow_Means[6] *= SideWindowWeight_Mean_Cardinal;
      Output.SideWindow_Means[7] *= SideWindowWeight_Mean_Cardinal;
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
      Block.Influence = GetCovarianceCoherence_Inverse(CovarianceMat);
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
      float SumInfluence = 0.0;

      [unroll]
      for (int i0 = 0; i0 < SideWindowsCount; i0++)
      {
         GetSideWindow_Bilateral(i0, SharedData, SideWindows[i0]);
         if (SideWindows[i0].SumWeight > 0.0)
         {
            // Normalize the sum.
            float2 Sum = SideWindows[i0].Sum / SideWindows[i0].SumWeight;

            // Weighted sum by influence.
            WindowMean += (Sum * SideWindows[i0].Influence);
            SumInfluence += SideWindows[i0].Influence;
         }
      }

      WindowMean = (SumInfluence > 0.0) ? WindowMean / SumInfluence : 0.0;

      return WindowMean;
   }
