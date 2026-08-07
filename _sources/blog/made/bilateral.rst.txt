
Variance-Weighted Adaptive, Multilevel, Side-Window Bilateral Upsampling on the GPU
===================================================================================

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

Side Windows with Max-Selection
-------------------------------

Conventional bilateral filters use a single centered window, which captures pixels from both sides of edges, causing blurring. This implementation instead uses **eight shifted side windows** covering all cardinal directions and corners.

For each side window :math:`W_i` (where :math:`i \in \{1, 2, ..., 8\}`), the algorithm:

#. Computes a weighted mean using Jaccard similarities as weights
#. Measures the similarity between this window's mean and the guide reference
#. Selects the window with maximum similarity

This max-selection approach:

* **Preserves edges** by selecting the window best aligned with local structure
* **Reduces artifacts** by choosing the most similar region
* **Improves robustness** through explicit similarity measurement

Algorithm Implementation
------------------------

The implementation follows these steps:

#. **Shared Data Gathering**: Collect a 3x3 neighborhood with 2x pixel footprint (lines 324-336)
#. **Jaccard Similarity**: Compute similarity between each sample and guide reference (line 332)
#. **Side Window Precomputation**: Compute means for 8 side windows (lines 361-389) - note these are precomputed but unused in final selection
#. **Max-Similarity Selection**: For each window, compute weighted mean using Jaccard similarities, then select window with maximum similarity to reference (lines 470-491)
#. **Return**: The mean from the best-matching window (line 493)

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

Mathematical Formulations
-------------------------

.. describe:: Jaccard similarity

   .. math::

      w_{\mathrm{similarity}}(j) = \frac{{(A \cdot B)}}{{(A \cdot A)} + {(B \cdot B)} - {(A \cdot B)}}

.. describe:: Side Window Bilateral Mean

   .. math::

      \mu_{W_i} = \frac{\sum_{j \in W_i} \mathbf{p}_j \cdot w_{\mathrm{similarity}}(j)}{\sum_{j \in W_i} w_{\mathrm{similarity}}(j)}

.. describe:: Final Selection

   .. math::

      \mu_{\mathrm{final}} = \mu_{W_i} \quad \text{where} \quad i = \arg\max(\mathrm{Similarity}(\mu_{W_i}, \mathrm{Reference}))

Helper Math Functions
---------------------

The implementation includes several helper functions for data conversion and similarity computation:

.. code-block:: hlsl
   :caption: Helper Math Functions (Vector Similarity and Lorentzian)

   #define TEMPLATE_DATACONV(DATA_TYPE, LENGTH) \
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
   TEMPLATE_DATACONV(float, 1)
   TEMPLATE_DATACONV(float2, 2)
   TEMPLATE_DATACONV(float3, 3)
   TEMPLATE_DATACONV(float4, 4)

   float GetSimilarityJaccard_Fast(float DotAB, float DotAA, float DotBB)
   {
      float D = (DotAA + DotBB) - DotAB;
      float Similarity = (abs(D) > 0.0)
         ? saturate(SNORMtoUNORM_FLT1(DotAB / D))
         : 1.0;

      return Similarity;
   }

Main Function
-------------

The main function :code:`GetSelfBilateralUpsample_FLT2()` implements the complete bilateral upsampling algorithm:

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
      int SideWindow_Size;
      float2 SideWindow_Means[8];

      // Shared for final calculation.
      float2 Reference;
   };

   struct SideWindow_Bilateral
   {
      int Masks[9];

      float2 Sum;
      float SumWeight;
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
         1 1 1       1 1 1       1 0 0       0 0 1
         1 1 0       0 1 1       1 1 0       0 1 1
         1 0 0       0 0 1       1 1 1       1 1 1
      */

      const int SideWindowSize = 6;
      const float SideWindowWeight = 1.0 / float(SideWindowSize);

      Output.SideWindow_Size = SideWindowSize;

      float2 QuadHalf[6];
      QuadHalf[0] = Output.ArrayImages[0] + Output.ArrayImages[1]; // Vertical Top-Left       (TL)
      QuadHalf[1] = Output.ArrayImages[3] + Output.ArrayImages[4]; // Vertical Top-Mid        (TM)
      QuadHalf[2] = Output.ArrayImages[6] + Output.ArrayImages[7]; // Vertical Top-Right      (TR)
      QuadHalf[3] = Output.ArrayImages[1] + Output.ArrayImages[2]; // Vertical Bottom-Left    (BL)
      QuadHalf[4] = Output.ArrayImages[4] + Output.ArrayImages[5]; // Vertical Bottom-Mid     (BM)
      QuadHalf[5] = Output.ArrayImages[7] + Output.ArrayImages[8]; // Vertical Bottom-Right   (BR)

      float2 QuadFull[4];
      QuadFull[0] = (QuadHalf[0] + QuadHalf[1]) + Output.ArrayImages[6]; // NW & N: [0 + 1] + [3 + 4] + [6]
      QuadFull[1] = (QuadHalf[1] + QuadHalf[2]) + Output.ArrayImages[8]; // NE & E: [3 + 4] + [6 + 7] + [8]
      QuadFull[2] = (QuadHalf[3] + QuadHalf[4]) + Output.ArrayImages[0]; // SW & W: [1 + 2] + [4 + 5] + [0]
      QuadFull[3] = (QuadHalf[4] + QuadHalf[5]) + Output.ArrayImages[2]; // SE & S: [4 + 5] + [7 + 8] + [2]

      float2 Sums[ArraySideWindowsLength];
      Sums[0] = QuadFull[0] + Output.ArrayImages[2]; // NW:  [0 + 1] + [3 + 4] + [6] + [2]
      Sums[1] = QuadFull[1] + Output.ArrayImages[0]; // NE:  [3 + 4] + [6 + 7] + [8] + [0]
      Sums[2] = QuadFull[2] + Output.ArrayImages[8]; // SW:  [1 + 2] + [4 + 5] + [0] + [8]
      Sums[3] = QuadFull[3] + Output.ArrayImages[6]; // SE:  [4 + 5] + [7 + 8] + [2] + [6]
      Sums[4] = QuadFull[0] + Output.ArrayImages[7]; // N:   [0 + 1] + [3 + 4] + [6] + [7]
      Sums[5] = QuadFull[3] + Output.ArrayImages[1]; // S:   [4 + 5] + [7 + 8] + [2] + [1]
      Sums[6] = QuadFull[2] + Output.ArrayImages[3]; // W:   [1 + 2] + [4 + 5] + [0] + [3]
      Sums[7] = QuadFull[1] + Output.ArrayImages[5]; // E:   [3 + 4] + [6 + 7] + [8] + [5]

      [unroll]
      for (int i = 0; i < ArraySideWindowsLength; i++)
      {
         Output.SideWindow_Means[i] = Sums[i] * SideWindowWeight;
      }
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

      // Calculate Side Winder filter
      float2 NearestWindow = 0.0;
      float MaxSimilarity = 0.0;

      // Pre-compute Reference.Reference
      float DotRR = dot(SharedData.Reference, SharedData.Reference);

      [unroll]
      for (int i0 = 0; i0 < SideWindowsCount; i0++)
      {
         GetSideWindow_Bilateral(i0, SharedData, SideWindows[i0]);

         [flatten]
         if (SideWindows[i0].SumWeight > 0.0)
         {
            float2 SideWindowMean = SideWindows[i0].Sum / SideWindows[i0].SumWeight;
            float Similarity = GetSimilarityJaccard_Fast(
               dot(SideWindowMean, SharedData.Reference),
               dot(SideWindowMean, SideWindowMean),
               DotRR
            );

            if (Similarity > MaxSimilarity)
            {
               MaxSimilarity = Similarity;
               NearestWindow = SideWindowMean;
            }
         }
      }

      return NearestWindow;
   }
