
Side-Window Bilateral Upsampling on the GPU
===========================================

This document describes the actual implementation of a variance-weighted adaptive, multilevel, side-window bilateral upsampling filter for motion vectors. The filter uses Jaccard similarity for range weighting and max-similarity selection to preserve edges and reduce artifacts.

.. seealso::

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. *ACM SIGGRAPH 2007 Papers*, 96. https://doi.org/10.1145/1275808.1276497

   Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition* (CVPR), 8758-8766.

Introduction
------------

This implementation performs bilateral upsampling using a guide image to determine pixel similarity. Unlike traditional bilateral filters that use fixed spatial or intensity distances, this approach uses **Jaccard similarity** to measure how similar each sample is to the guide reference, then selects the window with maximum similarity.

The algorithm follows these key steps:

#. **Shared Data Gathering**: Collect a 3x3 neighborhood with 2x pixel footprint
#. **Jaccard Similarity**: Compute similarity between each sample and guide reference
#. **Side Window Precomputation**: Compute means for 8 side windows (precomputed but unused in final selection)
#. **Max-Similarity Selection**: For each window, compute weighted mean using Jaccard similarities, then select window with maximum similarity to reference
#. **Return**: The mean from the best-matching window

Bilateral Upsampling
--------------------

Bilateral upsampling interpolates a low-resolution target image using a high-resolution guide image. Unlike linear interpolation, which assumes uniform smoothness, bilateral filtering preserves structural edges by weighting pixel contributions based on intensity similarity to the guide image.

This implementation uses the guide image to compute Jaccard similarity weights, which measure how similar each low-resolution pixel is to the guide reference. These weights are then used to compute a weighted average that preserves edges.

Jaccard Similarity for Range Weighting
--------------------------------------

The Jaccard similarity metric measures the similarity between two vectors. For this implementation, it's used to compare each sample pixel with the guide reference pixel.

The Jaccard similarity is computed as:

.. math::

   w_{\mathrm{similarity}}(j) = \frac{A \cdot B}{(A \cdot A) + (B \cdot B) - (A \cdot B)}

This metric is bounded between 0 and 1, where:

* **1** indicates perfect similarity between vectors
* **0** indicates no similarity

The helper function :code:`GetSimilarityJaccard_Fast()` implements this with proper bounds checking:

.. math::

   \mathrm{Similarity} = \begin{cases}
   \frac{(A \cdot B)}{{(A \cdot A)} + {(B \cdot B)} - {(A \cdot B)}} & \text{if } |D| > 0 \\
      1.0 & \text{otherwise}
   \end{cases}

Side Windows with CoV Selection
-------------------------------

Conventional bilateral filters use a single centered window, which captures pixels from both sides of edges, causing blurring. This implementation instead uses **eight shifted side windows** covering all cardinal directions and corners to select the window with the least **Van Valen's Coefficient of Variation (CoV)**, ensuring better alignment with local structure.

For each side window :math:`W_i` (where :math:`i \in \{1, 2, ..., 8\}`), the algorithm:

#. Computes a weighted mean using Jaccard similarities as weights
#. Calculates the **Coefficient of Variation (CoV)** of the window's pixel contributions
#. Selects the window with the **minimum CoV**

This CoV-based selection approach:

* **Preserves edges** by selecting the window with the least relative variability
* **Reduces artifacts** by avoiding regions with high relative pixel variability
* **Improves robustness** by focusing on proportionally homogeneous regions

Algorithm Implementation
------------------------

The implementation follows these steps:

#. **Shared Data Gathering**: Collect a 3x3 neighborhood with 2x pixel footprint
#. **Jaccard Similarity**: Compute similarity between each sample and guide reference
#. **Side Window Precomputation**: Compute means for 8 side windows
#. **CoV-Based Selection**: For each window, compute weighted mean using Jaccard similarities and calculate **Van Valen's Coefficient of Variation (CoV)**. Select the window with the minimum CoV
#. **Return**: The mean from the window with the least CoV

Side Window Masks
-----------------

The implementation uses eight side window masks with the following patterns:

.. math::

   \begin{array}{cc}
   \boldsymbol{NW} = \begin{bmatrix} 1 & 1 & 1 \\ 1 & 1 & 0 \\ 1 & 0 & 0 \end{bmatrix} &
   \boldsymbol{NE} = \begin{bmatrix} 1 & 1 & 1 \\ 0 & 1 & 1 \\ 0 & 0 & 1 \end{bmatrix} \\
   \boldsymbol{SW} = \begin{bmatrix} 1 & 0 & 0 \\ 1 & 1 & 0 \\ 1 & 1 & 1 \end{bmatrix} &
   \boldsymbol{SE} = \begin{bmatrix} 0 & 0 & 1 \\ 0 & 1 & 1 \\ 1 & 1 & 1 \end{bmatrix}
   \end{array}

.. math::

   \begin{array}{cc}
   \boldsymbol{N} = \begin{bmatrix} 1 & 1 & 1 \\ 1 & 1 & 1 \\ 0 & 0 & 0 \end{bmatrix} &
   \boldsymbol{S} = \begin{bmatrix} 0 & 0 & 0 \\ 1 & 1 & 1 \\ 1 & 1 & 1 \end{bmatrix} \\
   \boldsymbol{W} = \begin{bmatrix} 1 & 1 & 0 \\ 1 & 1 & 0 \\ 1 & 1 & 0 \end{bmatrix} &
   \boldsymbol{E} = \begin{bmatrix} 0 & 1 & 1 \\ 0 & 1 & 1 \\ 0 & 1 & 1 \end{bmatrix}
   \end{array}

These masks define which pixels contribute to each side window, covering all cardinal directions and corners.

Van Valen's Coefficient of Variation (CoV)
------------------------------------------

In this implementation, **Van Valen's Coefficient of Variation (CoV)** is used to determine the best-matching side window for upsampling. CoV measures the relative spread of pixel values within a window, normalized by the mean, providing a more robust metric for homogeneity.

The CoV is approximated as:

.. math::

   \text{CoV} \approx \sqrt{\frac{\text{Variance}}{\mu \cdot \mu}}

where:

* :math:`\text{Variance}` is the spread of pixel values in the window.
* :math:`\mu` is the weighted mean of the window's pixels (computed using Jaccard similarity as weights).

The algorithm selects the window with the **minimum CoV**, ensuring the most homogeneous region is chosen for upsampling. This approach improves edge preservation and reduces artifacts by avoiding regions with high relative variability.

Mathematical Formulations
-------------------------

.. note::

   This implementation now uses **Van Valen's Coefficient of Variation (CoV)** for window selection instead of raw variance. The window with the least CoV is chosen to ensure the most homogeneous region is used for upsampling.

.. describe:: Jaccard similarity

   .. math::

      w_{\mathrm{similarity}}(j) = \frac{A \cdot B}{(A \cdot A) + (B \cdot B) - (A \cdot B)}

.. describe:: Side Window Bilateral Mean

   .. math::

      \mu_{W_i} = \frac{\sum_{j \in W_i} \mathbf{p}_j \cdot w_{\mathrm{similarity}}(j)}{\sum_{j \in W_i} w_{\mathrm{similarity}}(j)}

.. describe:: Van Valen's Coefficient of Variation (CoV)

   .. math::

      \text{CoV} \approx \sqrt{\frac{\text{Variance}}{\mu \cdot \mu}}

.. describe:: Window Selection (CoV-Based)

   The algorithm selects the window with the **minimum CoV** to ensure the most homogeneous region is chosen for upsampling:

   .. math::

      \mu_{\mathrm{final}} = \mu_{W_i} \quad \text{where} \quad i = \arg\min(\text{CoV}(W_i))

   This approach improves edge preservation and reduces artifacts by focusing on regions where pixel values are proportionally consistent.

Helper Math Functions
---------------------

The implementation includes several helper functions for data conversion and similarity computation:

.. code-block:: hlsl
   :caption: Helper Math Functions (Vector Similarity and Lorentzian)

   #define TEMPLATE_DATA_CONV(DATA_TYPE, LENGTH) \
      DATA_TYPE UNORMtoSNORM_FLT##LENGTH(DATA_TYPE X) \
      { \
         return (X * (DATA_TYPE)2.0) - (DATA_TYPE)1.0; \
      } \
      \
      DATA_TYPE SNORMtoUNORM_FLT##LENGTH(DATA_TYPE X) \
      { \
         return (X * (DATA_TYPE)0.5) + (DATA_TYPE)0.5; \
      } \
      \
      DATA_TYPE FP16toSNORM_FLT##LENGTH(DATA_TYPE X) \
      { \
         return X / (DATA_TYPE)GetFP16Max(); \
      } \
      \
      DATA_TYPE SNORMtoFP16_FLT##LENGTH(DATA_TYPE X) \
      { \
         return X * (DATA_TYPE)GetFP16Max(); \
      }

   // Instantiate template over vector dimensions
   TEMPLATE_DATA_CONV(float, 1)
   TEMPLATE_DATA_CONV(float2, 2)
   TEMPLATE_DATA_CONV(float3, 3)
   TEMPLATE_DATA_CONV(float4, 4)

   float GetSimilarityJaccard_Fast(bool OutputSigned, float DotAB, float DotAA, float DotBB)
   {
      float D = (DotAA + DotBB) - DotAB;
      float S = DotAB / D;

      if (!OutputSigned)
      {
         S = saturate(SNORMtoUNORM_FLT1(S));
      }

      S = (D == 0.0) ? 1.0 : S;

      return S;
   }

   float GetCoefficientVariation_VV(float2 Mean, float2 Trace)
   {
      float N = Trace.x + Trace.y;
      float D = dot(Mean, Mean);
      float VV = (abs(N) > 0.0) ? rsqrt(D / N) : 0.0;

      return VV;
   }

Main Function
-------------

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
      int SideWindowSize;

      // Window (Local) information.
      int ArrayImageLength;
      float2 ArrayGuides[9];

      // Guide Windows (Side Windows, but as Guides).
      float2 ArrayWindowGuides[8];
      float2 ArrayWindowImages[8];
      float ArrayWindowWeightSums[8];
   };

   struct SideWindow_Bilateral
   {
      int Masks[9];

      float2 Sum;
      float Variance;
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

      // Precompute (static)
      float2 PixelSize = fwidth(Tex.xy);

      /*
         Gather samples:

         0 3 6 [ North West | North  | North East ]
         1 4 7 [    West    | Center |    East    ]
         2 5 8 [ South West | South  | South East ]
      */

      // Initialize counter here
      float2 ArrayImages[ArrayImageLength];
      float ArrayWeights[ArrayImageLength];
      int ImageIndex0 = 0;

      [unroll]
      for (int x0 = -1; x0 <= 1; x0++)
      {
         [unroll]
         for (int y0 = -1; y0 <= 1; y0++)
         {
            // *2 because the lower sample takes a 2 texel footprint.
            float2 Delta = float2(x0, y0) * 2.0;
            float4 Offset = CShade_PadFloat2(Tex + (Delta * PixelSize));

            // Sampling.
            float2 GuideSample = tex2Dlod(Guide, Offset).xy;
            float2 ImageSample = tex2Dlod(Image, Offset).xy;

            // Create variables for our distance calculation.
            float DotAB = dot(GuideSample, ImageSample);
            float DotAA = dot(ImageSample, ImageSample);
            float DotBB = dot(GuideSample, GuideSample);

            // Compute the similarity
            float Similarity = GetSimilarityJaccard_Fast(false, DotAB, DotAA, DotBB);

            // This is for our Side Window calculation.
            Output.ArrayGuides[ImageIndex0] = GuideSample;
            ArrayImages[ImageIndex0] = ImageSample * Similarity;
            ArrayWeights[ImageIndex0] = Similarity;

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
         1 1 1       1 1 1       1 0 0       0 0 1
         1 1 0       0 1 1       1 1 0       0 1 1
         1 0 0       0 0 1       1 1 1       1 1 1
      */

      const int SideWindowSize = 6;
      const float SideWindowWeight = 1.0 / float(SideWindowSize);

      Output.SideWindowSize = SideWindowSize;

      float2 QuadHalfGuides[6];
      QuadHalfGuides[0] = Output.ArrayGuides[0] + Output.ArrayGuides[1]; // Vertical Top-Left       (TL)
      QuadHalfGuides[1] = Output.ArrayGuides[3] + Output.ArrayGuides[4]; // Vertical Top-Mid        (TM)
      QuadHalfGuides[2] = Output.ArrayGuides[6] + Output.ArrayGuides[7]; // Vertical Top-Right      (TR)
      QuadHalfGuides[3] = Output.ArrayGuides[1] + Output.ArrayGuides[2]; // Vertical Bottom-Left    (BL)
      QuadHalfGuides[4] = Output.ArrayGuides[4] + Output.ArrayGuides[5]; // Vertical Bottom-Mid     (BM)
      QuadHalfGuides[5] = Output.ArrayGuides[7] + Output.ArrayGuides[8]; // Vertical Bottom-Right   (BR)

      float2 QuadFullGuides[4];
      QuadFullGuides[0] = (QuadHalfGuides[0] + QuadHalfGuides[1]) + Output.ArrayGuides[6]; // NW & N: [0 + 1] + [3 + 4] + [6]
      QuadFullGuides[1] = (QuadHalfGuides[1] + QuadHalfGuides[2]) + Output.ArrayGuides[8]; // NE & E: [3 + 4] + [6 + 7] + [8]
      QuadFullGuides[2] = (QuadHalfGuides[3] + QuadHalfGuides[4]) + Output.ArrayGuides[0]; // SW & W: [1 + 2] + [4 + 5] + [0]
      QuadFullGuides[3] = (QuadHalfGuides[4] + QuadHalfGuides[5]) + Output.ArrayGuides[2]; // SE & S: [4 + 5] + [7 + 8] + [2]

      Output.ArrayWindowGuides[0] = (QuadFullGuides[0] + Output.ArrayGuides[2]) * SideWindowWeight; // NW:    [0 + 1] + [3 + 4] + [6] + [2]
      Output.ArrayWindowGuides[1] = (QuadFullGuides[1] + Output.ArrayGuides[0]) * SideWindowWeight; // NE:    [3 + 4] + [6 + 7] + [8] + [0]
      Output.ArrayWindowGuides[2] = (QuadFullGuides[2] + Output.ArrayGuides[8]) * SideWindowWeight; // SW:    [1 + 2] + [4 + 5] + [0] + [8]
      Output.ArrayWindowGuides[3] = (QuadFullGuides[3] + Output.ArrayGuides[6]) * SideWindowWeight; // SE:    [4 + 5] + [7 + 8] + [2] + [6]
      Output.ArrayWindowGuides[4] = (QuadFullGuides[0] + Output.ArrayGuides[7]) * SideWindowWeight; // N:     [0 + 1] + [3 + 4] + [6] + [7]
      Output.ArrayWindowGuides[5] = (QuadFullGuides[3] + Output.ArrayGuides[1]) * SideWindowWeight; // S:     [4 + 5] + [7 + 8] + [2] + [1]
      Output.ArrayWindowGuides[6] = (QuadFullGuides[2] + Output.ArrayGuides[3]) * SideWindowWeight; // W:     [1 + 2] + [4 + 5] + [0] + [3]
      Output.ArrayWindowGuides[7] = (QuadFullGuides[1] + Output.ArrayGuides[5]) * SideWindowWeight; // E:     [3 + 4] + [6 + 7] + [8] + [5]

      float2 QuadHalfImages[6];
      QuadHalfImages[0] = ArrayImages[0] + ArrayImages[1]; // Vertical Top-Left       (TL)
      QuadHalfImages[1] = ArrayImages[3] + ArrayImages[4]; // Vertical Top-Mid        (TM)
      QuadHalfImages[2] = ArrayImages[6] + ArrayImages[7]; // Vertical Top-Right      (TR)
      QuadHalfImages[3] = ArrayImages[1] + ArrayImages[2]; // Vertical Bottom-Left    (BL)
      QuadHalfImages[4] = ArrayImages[4] + ArrayImages[5]; // Vertical Bottom-Mid     (BM)
      QuadHalfImages[5] = ArrayImages[7] + ArrayImages[8]; // Vertical Bottom-Right   (BR)

      float2 QuadFullImages[4];
      QuadFullImages[0] = (QuadHalfImages[0] + QuadHalfImages[1]) + ArrayImages[6]; // NW & N: [0 + 1] + [3 + 4] + [6]
      QuadFullImages[1] = (QuadHalfImages[1] + QuadHalfImages[2]) + ArrayImages[8]; // NE & E: [3 + 4] + [6 + 7] + [8]
      QuadFullImages[2] = (QuadHalfImages[3] + QuadHalfImages[4]) + ArrayImages[0]; // SW & W: [1 + 2] + [4 + 5] + [0]
      QuadFullImages[3] = (QuadHalfImages[4] + QuadHalfImages[5]) + ArrayImages[2]; // SE & S: [4 + 5] + [7 + 8] + [2]

      Output.ArrayWindowImages[0] = QuadFullImages[0] + ArrayImages[2]; // NW:    [0 + 1] + [3 + 4] + [6] + [2]
      Output.ArrayWindowImages[1] = QuadFullImages[1] + ArrayImages[0]; // NE:    [3 + 4] + [6 + 7] + [8] + [0]
      Output.ArrayWindowImages[2] = QuadFullImages[2] + ArrayImages[8]; // SW:    [1 + 2] + [4 + 5] + [0] + [8]
      Output.ArrayWindowImages[3] = QuadFullImages[3] + ArrayImages[6]; // SE:    [4 + 5] + [7 + 8] + [2] + [6]
      Output.ArrayWindowImages[4] = QuadFullImages[0] + ArrayImages[7]; // N:     [0 + 1] + [3 + 4] + [6] + [7]
      Output.ArrayWindowImages[5] = QuadFullImages[3] + ArrayImages[1]; // S:     [4 + 5] + [7 + 8] + [2] + [1]
      Output.ArrayWindowImages[6] = QuadFullImages[2] + ArrayImages[3]; // W:     [1 + 2] + [4 + 5] + [0] + [3]
      Output.ArrayWindowImages[7] = QuadFullImages[1] + ArrayImages[5]; // E:     [3 + 4] + [6 + 7] + [8] + [5]

      float2 QuadHalfWeights[6];
      QuadHalfWeights[0] = ArrayWeights[0] + ArrayWeights[1]; // Vertical Top-Left        (TL)
      QuadHalfWeights[1] = ArrayWeights[3] + ArrayWeights[4]; // Vertical Top-Mid         (TM)
      QuadHalfWeights[2] = ArrayWeights[6] + ArrayWeights[7]; // Vertical Top-Right       (TR)
      QuadHalfWeights[3] = ArrayWeights[1] + ArrayWeights[2]; // Vertical Bottom-Left     (BL)
      QuadHalfWeights[4] = ArrayWeights[4] + ArrayWeights[5]; // Vertical Bottom-Mid      (BM)
      QuadHalfWeights[5] = ArrayWeights[7] + ArrayWeights[8]; // Vertical Bottom-Right    (BR)

      float2 QuadFullWeights[4];
      QuadFullWeights[0] = (QuadHalfWeights[0] + QuadHalfWeights[1]) + ArrayWeights[6]; // NW & N: [0 + 1] + [3 + 4] + [6]
      QuadFullWeights[1] = (QuadHalfWeights[1] + QuadHalfWeights[2]) + ArrayWeights[8]; // NE & E: [3 + 4] + [6 + 7] + [8]
      QuadFullWeights[2] = (QuadHalfWeights[3] + QuadHalfWeights[4]) + ArrayWeights[0]; // SW & W: [1 + 2] + [4 + 5] + [0]
      QuadFullWeights[3] = (QuadHalfWeights[4] + QuadHalfWeights[5]) + ArrayWeights[2]; // SE & S: [4 + 5] + [7 + 8] + [2]

      Output.ArrayWindowWeightSums[0] = QuadFullWeights[0] + ArrayWeights[2]; // NW:  [0 + 1] + [3 + 4] + [6] + [2]
      Output.ArrayWindowWeightSums[1] = QuadFullWeights[1] + ArrayWeights[0]; // NE:  [3 + 4] + [6 + 7] + [8] + [0]
      Output.ArrayWindowWeightSums[2] = QuadFullWeights[2] + ArrayWeights[8]; // SW:  [1 + 2] + [4 + 5] + [0] + [8]
      Output.ArrayWindowWeightSums[3] = QuadFullWeights[3] + ArrayWeights[6]; // SE:  [4 + 5] + [7 + 8] + [2] + [6]
      Output.ArrayWindowWeightSums[4] = QuadFullWeights[0] + ArrayWeights[7]; // N:   [0 + 1] + [3 + 4] + [6] + [7]
      Output.ArrayWindowWeightSums[5] = QuadFullWeights[3] + ArrayWeights[1]; // S:   [4 + 5] + [7 + 8] + [2] + [1]
      Output.ArrayWindowWeightSums[6] = QuadFullWeights[2] + ArrayWeights[3]; // W:   [1 + 2] + [4 + 5] + [0] + [3]
      Output.ArrayWindowWeightSums[7] = QuadFullWeights[1] + ArrayWeights[5]; // E:   [3 + 4] + [6 + 7] + [8] + [5]
   }

   void GetSideWindow_Bilateral(
      in int SideWindowIndex,
      in SharedData_SideWindow_Bilateral Input,
      inout SideWindow_Bilateral Block
   )
   {
      // Compute sample weight
      const float Weight = 1.0 / (float(Input.SideWindowSize - 1));

      float2 MeanGuide = Input.ArrayWindowGuides[SideWindowIndex];
      float2 MeanImage = Input.ArrayWindowImages[SideWindowIndex];
      float WeightSum = Input.ArrayWindowWeightSums[SideWindowIndex];
      float2 Moments = 0.0;

      [unroll]
      for (int i0 = 0; i0 < Input.ArrayImageLength; i0++)
      {
         if (Block.Masks[i0] == 1)
         {
            float2 Error = Input.ArrayGuides[i0] - MeanGuide;
            Moments += (Error * Error);
         }
      }

      // Compute variance
      Block.Sum = MeanImage / WeightSum;
      Block.Variance = GetCoefficientVariation_VV(MeanGuide, Moments * Weight);
   }

   float2 GetSideWindowBilateralUpsample_FLT2(
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
         1 1 1       1 1 1       1 0 0       0 0 1
         1 1 0       0 1 1       1 1 0       0 1 1
         1 0 0       0 0 1       1 1 1       1 1 1
      */

      // Initialize our side windows
      SideWindow_Bilateral SideWindows[SideWindowsCount];
      SideWindows[0].Masks = { 1, 1, 1, 1, 1, 0, 1, 0, 0 }; // NW
      SideWindows[1].Masks = { 1, 0, 0, 1, 1, 0, 1, 1, 1 }; // NE
      SideWindows[2].Masks = { 1, 1, 1, 0, 1, 1, 0, 0, 1 }; // SW
      SideWindows[3].Masks = { 0, 0, 1, 0, 1, 1, 1, 1, 1 }; // SE
      SideWindows[4].Masks = { 1, 1, 0, 1, 1, 0, 1, 1, 0 }; // N
      SideWindows[5].Masks = { 0, 1, 1, 0, 1, 1, 0, 1, 1 }; // S
      SideWindows[6].Masks = { 1, 1, 1, 1, 1, 1, 0, 0, 0 }; // W
      SideWindows[7].Masks = { 0, 0, 0, 1, 1, 1, 1, 1, 1 }; // E

      /*
         Calculate Side Window filter
      */

      bool AVariance = false;
      float MinVariance;
      float2 NearestWindow = 0.0;

      [unroll]
      for (int i0 = 0; i0 < SideWindowsCount; i0++)
      {
         GetSideWindow_Bilateral(i0, SharedData, SideWindows[i0]);

         if (SharedData.ArrayWindowWeightSums[i0] > 0.0)
         {
            [flatten]
            if ((AVariance == false) || (SideWindows[i0].Variance < MinVariance))
            {
               AVariance = true;
               MinVariance = SideWindows[i0].Variance;
               NearestWindow = SideWindows[i0].Sum;
            }
         }
      }

      return NearestWindow;
   }
