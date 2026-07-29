
Dense Lucas-Kanade Optical Flow on the GPU
==========================================

Optical flow estimates motion between consecutive video frames. It powers object detection, motion estimation, video compression, and special effects. This guide covers the Lucas-Kanade method with practical GPU implementation details.

Overview
--------

This document explains the Lucas-Kanade optical flow algorithm and its adaptive-weighted variant implemented in HLSL for GPU execution. It balances theory with implementation guidance for researchers and developers.

The document is organized into six sections:

#. **Core Theory**: Explains the Brightness Constancy Assumption and Optical Flow Equation
#. **The Aperture Problem**: Shows why single-pixel motion is ambiguous
#. **Lucas-Kanade Solution**: Derives the least-squares method to solve the aperture problem
#. **Advanced Enhancements**: Details bilateral weighting, anisotropy regularization, and pyramid approaches
#. **Implementation**: Provides the complete HLSL source code
#. **Technical Details**: Documents key implementation choices

Core Theory
-----------

Optical flow relies on two fundamental assumptions about how objects appear and move:

#. **Brightness constancy**: An object's intensity remains approximately constant between frames
#. **Small motion**: Objects move only a few pixels between consecutive frames

These assumptions lead to the Brightness Constancy Assumption equation:

.. math::

   I(x, y, t) = I(x + u, y + v, t + 1)

where :math:`I(x, y, t)` is the image intensity at position :math:`(x, y)` and time :math:`t`, and :math:`(u, v)` is the motion vector we want to find.

To solve for :math:`u` and :math:`v`, we approximate the right side using a first-order Taylor expansion around :math:`(x, y, t)`:

.. math::

   I(x + u, y + v, t + 1) \approx I(x, y, t) + \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

Substituting this back and simplifying gives the Optical Flow Equation:

.. math::

   \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v = -\frac{\partial I}{\partial t}

This equation relates spatial gradients (:math:`I_x, I_y`) to temporal change (:math:`I_t`) and our unknown motion vector (:math:`u, v`).

The Aperture Problem
--------------------

The aperture problem demonstrates why single-pixel motion is ambiguous. When viewing motion through a small opening, we cannot distinguish between different motion directions that produce the same local appearance change.

For example, sliding a straight string through a small hole appears identical regardless of whether you move it horizontally, vertically, or diagonally. Only the component perpendicular to the string's orientation is visible.

Mathematically, the Optical Flow Equation provides one equation with two unknowns:

.. math::

   I_x u + I_y v = -I_t

This has infinitely many solutions. Plotting them forms a line in :math:`(u, v)` space, showing the true motion direction is ambiguous.

Lucas-Kanade Solution
---------------------

The Lucas-Kanade method solves the aperture problem by using information from a small neighborhood around each pixel. Instead of one equation, we collect multiple equations from nearby pixels and solve them together.

We form a system of equations in matrix form:

.. math::

   \begin{bmatrix}
   I_{x_1} & I_{y_1} \\
   I_{x_2} & I_{y_2} \\
   I_{x_3} & I_{y_3}
   \end{bmatrix}
   \begin{bmatrix}
   u \\
   v
   \end{bmatrix} =
   \begin{bmatrix}
   -I_{t_1} \\
   -I_{t_2} \\
   -I_{t_3}
   \end{bmatrix}

This system is typically overdetermined (more equations than unknowns). We solve it using least squares by multiplying both sides by the transpose of the matrix:

.. math::

   A^T A \begin{bmatrix} u \\ v \end{bmatrix} = A^T b

where :math:`A` is the matrix of spatial gradients and :math:`b` is the temporal gradient vector.

The least-squares solution becomes:

.. math::

   \begin{bmatrix} u \\ v \end{bmatrix} = (A^T A)^{-1} A^T b

Expanding this gives the final formula for optical flow at each pixel:

.. math::

   \begin{bmatrix} u \\ v \end{bmatrix} =
   \begin{bmatrix}
   \sum I_x^2 & \sum I_x I_y \\
   \sum I_x I_y & \sum I_y^2
   \end{bmatrix}^{-1}
   \begin{bmatrix}
   -\sum I_x I_t \\
   -\sum I_y I_t
   \end{bmatrix}

Advanced Enhancements
---------------------

Standard Lucas-Kanade treats all pixels in the neighborhood equally. The adaptive-weighted variant improves robustness by giving more influence to pixels that are similar to the center pixel in both color and intensity.

Bilateral Weighting
^^^^^^^^^^^^^^^^^^^

Bilateral weighting assigns each pixel a weight based on its similarity to the center pixel. We use the Dice similarity metric, which combines angular alignment and relative scale into a unified score.

The similarity is computed as:

.. math::

   \text{Similarity} = \text{saturate}\left(\frac{N}{D} + 0.5\right)

where:

.. math::

   N &= (T_r \cdot T_s) + (I_r \cdot I_s) \\
   D &= (T_s \cdot T_s) + (I_s \cdot I_s) + E

and :math:`E = (T_r \cdot T_r) + (I_r \cdot I_r)` is pre-computed for efficiency.

Key properties:

* Center pixel always receives weight 1.0 (perfect similarity to itself)
* Weights are normalized by dividing by the sum of all weights
* Normalized weights are applied to spatial and temporal gradients before accumulation
* This gives more influence to pixels that match the center pixel in color and intensity

Anisotropy Factor and Regularization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To ensure numerical stability, especially in low-texture regions, we add trace-scaled regularization to the structure tensor. This prevents matrix inversion failures while maintaining scale invariance across different image contrasts.

The regularization computes a damping factor :math:`\Lambda` that scales with the trace of the structure tensor:

.. math::

   \Lambda = \begin{cases}
   0 & \text{if } Tr > 0 \text{ (no regularization when gradients exist)} \\
   Tr - \frac{4Dt}{Tr} & \text{if } Tr \leq 0 \text{ (apply regularization)}
   \end{cases}

where:

* :math:`Tr = A[0] + A[1]` is the trace (sum of diagonal elements)
* :math:`Dt = (A[0] \times A[1]) - (A[2] \times A[2])` is the determinant
* :math:`A[0] = \sum I_x^2`, :math:`A[1] = \sum I_y^2`, :math:`A[2] = \sum I_x I_y`

The regularized structure tensor becomes:

.. math::

   \begin{bmatrix}
   A_{00} & A_{12} \\
   A_{12} & A_{11}
   \end{bmatrix} =
   \begin{bmatrix}
   A[0] + \Lambda & A[2] \\
   A[2] & A[1] + \Lambda
   \end{bmatrix}

This regularization is applied before inverting the structure tensor to solve for the optical flow vector.

Pyramid Approach (Conceptual)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While not implemented in the provided code, the pyramid approach extends Lucas-Kanade to handle large motions:

#. Create image pyramids for current and previous frames
#. Start with the smallest pyramid level (coarsest resolution)
#. Compute optical flow at this level
#. Use the result to initialize the next level
#. Repeat until the full-resolution image

This approach maintains the brightness constancy assumption while handling large displacements efficiently.

Implementation
--------------

The implementation provides the complete HLSL source code for the adaptive-weighted Lucas-Kanade algorithm. All code blocks are provided verbatim without modification.

.. note::

   The code contains **generic** functions. You may need to adapt parts to match your specific setup.

.. code-block:: hlsl
   :caption: Math Helper Functions

   /*
      Function to convert 2D row and column (0-indexed) to a 1D index.
      GridPos.x: The 0-indexed row number.
      GridPos.y: The 0-indexed column number.
      GridWidth: The total width of the grid (number of columns).
      Returns a 1D index.
   */
   int Get1DIndexFrom2D(int2 GridPos, int GridWidth)
   {
      return GridPos.x + (GridPos.y * GridWidth);
   }

   // Get the Half format distribution of bits
   // Sign Exponent Significand
   // x    xxxxx    xxxxxxxxxx
   float Calculate_FP16(int Sign, int Exponent, int Significand)
   {
      const int Bias = -15;
      const int MaxExponent = (Exponent - exp2(1)) + Bias;
      const int MaxSignificand = 1 + ((Significand - 1) / Significand);

      return (float)pow(-1, Sign) * (float)exp2(MaxExponent) * (float)MaxSignificand;
   }

   float GetFP16Min()
   {
      /*
         Sign  Exponent  Significand
         ----  --------  -----------
         0     00001     000000000
      */
      return Calculate_FP16(0, (int)exp2(0) + 1, (int)exp2(0));
   }

   float GetFP16Max()
   {
      /*
         Sign  Exponent Significand
         ----  -------- -----------
         0     11110    1111111111
      */
      return Calculate_FP16(0, (int)exp2(5), (int)exp2(10));
   }

   // [-HalfMax, HalfMax) -> [-1.0, 1.0)
   float2 FP16toSNORM_FLT2(float2 Value)
   {
      return Value / GetFP16Max();
   }

   // [-1.0, 1.0) -> [-HalfMax, HalfMax)
   float2 SNORMtoFP16_FLT2(float2 Value)
   {
      return Value * GetFP16Max();
   }

   float GetDiceIndex(
      float E,    // dot(T_r, T_r) + dot(I_r, I_r)
      float3 T_r, // T (Reference texture at center)
      float3 T_s, // T (Sample texture at current position)
      float3 I_r, // I (Reference texture at center)
      float3 I_s  // I (Sample texture at current position)
   )
   {
      float N = dot(T_r, T_s) + dot(I_r, I_s);
      float D = dot(T_s, T_s) + dot(I_s, I_s) + E;

      float S = (abs(D) > 0.0)
         ? saturate((N / D) + 0.5)
         : 1.0;

      return S;
   }

.. code-block:: hlsl
   :caption: SRGB to YUV

   /*
      Converts sRGB color space to YUV 4:4:4 format.

      "Recommendation T.832 (06/2019)". p. 185 Table D.6 - Pseudocode for function FwdColorFmtConvert1().
      https://www.itu.int/rec/T-REC-T.832
   */

   float3 SRGBtoYUV444(float3 SRGB, bool Normalize)
   {
      float3 YUV;
      YUV.z = SRGB.b - SRGB.r;
      YUV.y = -SRGB.r + SRGB.g - (YUV.z * 0.5);
      YUV.x = SRGB.g - (YUV.y * 0.5);
      return YUV;
   }

   /*
      Samples a texture and converts it from sRGB to YUV color space.
   */

   float3 GetPlanesYUV(sampler2D Image, float2 Tex)
   {
      float3 Color = tex2D(Image, Tex).rgb;
      Color = SRGBtoYUV444(Color);
      return Color;
   }

.. code-block:: hlsl
   :caption: Adaptive-Weighted Lucas-Kanade Optical Flow

   /*
      Lucas-Kanade optical flow with bilinear fetches. The algorithm outputs normalized displacements.

      ---

      Gauss-Newton Steepest Descent Inverse Additive Algorithm

      Baker, S., & Matthews, I. (2004). Lucas-kanade 20 years on: A unifying framework. International journal of computer vision, 56, 221-255.

      https://www.researchgate.net/publication/248602429_Lucas-Kanade_20_Years_On_A_Unifying_Framework_Part_1_The_Quantity_Approximated_the_Warp_Update_Rule_and_the_Gradient_Descent_Approximation

      ---

      Application of Lucas-Kanade algorithm with weight coefficient bilateral filtration for the digital image correlation method

      Titkov, V. V., Panin, S. V., Lyubutin, P. S., Chemezov, V. O., & Eremin, A. V. (2017). Application of Lucas-Kanade algorithm with weight coefficient bilateral filtration for the digital image correlation method. IOP Conference Series: Materials Science and Engineering, 177, 012039. https://doi.org/10.1088/1757-899X/177/1/012039
   */

   float2 GetLucasKanade(
      bool IsCoarse,
      float2 MainTex,
      float2 PixelSize,
      float2 Vectors,
      sampler2D SampleT,
      sampler2D SampleI
   )
   {
      /*
         * = Indecies for calculating the temporal gradient (IT)
         - = Unused indecies

         Template indecies:

            00- 01  02  03  04-
            05  06* 07* 08* 09
            10  11* 12* 13* 14
            15  16* 17* 18* 19
            20- 21  22  23  24-

         Template (Row, Column):

            (4, 0) (4, 1) (4, 2) (4, 3) (4, 4)
            (3, 0) (3, 1) (3, 2) (3, 3) (3, 4)
            (2, 0) (2, 1) (2, 2) (2, 3) (2, 4)
            (1, 0) (1, 1) (1, 2) (1, 3) (1, 4)
            (0, 0) (0, 1) (0, 2) (0, 3) (0, 4)
      */

      // Initiate Cache
      const int CacheWidth = 5;
      const int CacheIndexSize = CacheWidth * CacheWidth;
      float3 Cache[CacheIndexSize];

      // Loop over the starred template areas
      const int FetchGridWidth = 3;
      const int FetchGridSize = FetchGridWidth * FetchGridWidth;

      // .xy = TemplateGridPos; .zw = FetchPos
      const int4 P[FetchGridSize] =
      {
         // Process edge regions
         int4(int2(-1, -1), int2(1, 1)),
         int4(int2(1, -1), int2(3, 1)),
         int4(int2(-1, 1), int2(1, 3)),
         int4(int2(1, 1), int2(3, 3)),

         // Process cardinal regions
         int4(int2(0, -1), int2(2, 1)),
         int4(int2(-1, 0), int2(1, 2)),
         int4(int2(1, 0), int2(3, 2)),
         int4(int2(0, 1), int2(2, 3)),

         // Process center
         int4(int2(0, 0), int2(2, 2))
      };

      // Decode from FP16
      Vectors = clamp(FP16toSNORM_FLT2(Vectors), -1.0, 1.0);

      // Calculate warped texture coordinates & gradient information
      float2 WarpTex = 0.0;
      WarpTex = MainTex - 0.5; // Pull into [-0.5, 0.5) range
      WarpTex -= Vectors; // Inverse warp in the [-0.5, 0.5) range
      WarpTex = saturate(WarpTex + 0.5); // Push and clamp into [0.0, 1.0) range

      // Create Cache
      // This unrolled version samples and assigns to the Cache array.
      // The four corners of the 5x5 grid are skipped in the original code,
      // so they are not included in this rewrite.
      Cache[1] = GetPlanesYUV(SampleT, MainTex + (float2(-1, -2) * PixelSize));
      Cache[2] = GetPlanesYUV(SampleT, MainTex + (float2(0, -2) * PixelSize));
      Cache[3] = GetPlanesYUV(SampleT, MainTex + (float2(1, -2) * PixelSize));

      Cache[5] = GetPlanesYUV(SampleT, MainTex + (float2(-2, -1) * PixelSize));
      Cache[6] = GetPlanesYUV(SampleT, MainTex + (float2(-1, -1) * PixelSize));
      Cache[7] = GetPlanesYUV(SampleT, MainTex + (float2(0, -1) * PixelSize));
      Cache[8] = GetPlanesYUV(SampleT, MainTex + (float2(1, -1) * PixelSize));
      Cache[9] = GetPlanesYUV(SampleT, MainTex + (float2(2, -1) * PixelSize));

      Cache[10] = GetPlanesYUV(SampleT, MainTex + (float2(-2, 0) * PixelSize));
      Cache[11] = GetPlanesYUV(SampleT, MainTex + (float2(-1, 0) * PixelSize));
      Cache[12] = GetPlanesYUV(SampleT, MainTex + (float2(0, 0) * PixelSize));
      Cache[13] = GetPlanesYUV(SampleT, MainTex + (float2(1, 0) * PixelSize));
      Cache[14] = GetPlanesYUV(SampleT, MainTex + (float2(2, 0) * PixelSize));

      Cache[15] = GetPlanesYUV(SampleT, MainTex + (float2(-2, 1) * PixelSize));
      Cache[16] = GetPlanesYUV(SampleT, MainTex + (float2(-1, 1) * PixelSize));
      Cache[17] = GetPlanesYUV(SampleT, MainTex + (float2(0, 1) * PixelSize));
      Cache[18] = GetPlanesYUV(SampleT, MainTex + (float2(1, 1) * PixelSize));
      Cache[19] = GetPlanesYUV(SampleT, MainTex + (float2(2, 1) * PixelSize));

      Cache[21] = GetPlanesYUV(SampleT, MainTex + (float2(-1, 2) * PixelSize));
      Cache[22] = GetPlanesYUV(SampleT, MainTex + (float2(0, 2) * PixelSize));
      Cache[23] = GetPlanesYUV(SampleT, MainTex + (float2(1, 2) * PixelSize));

      // Initialize variables
      float3 A = 0.0;
      float2 B = 0.0;
      float WSum = 0.0;

      // Get center textures (this is for the spatial weighting)
      float3 T_C = Cache[Get1DIndexFrom2D(int2(2, 2), CacheWidth)];
      float3 I_C = GetPlanesYUV(SampleI, WarpTex);

      // Get center magnitudes
      float TT_II = dot(T_C, T_C) + dot(I_C, I_C);

      [unroll]
      for (int i = 0; i < FetchGridSize; i++)
      {
         // Get cached data
         float3 T_N = Cache[Get1DIndexFrom2D(P[i].zw + int2(0, -1), CacheWidth)];
         float3 T_S = Cache[Get1DIndexFrom2D(P[i].zw + int2(0, 1), CacheWidth)];
         float3 T_E = Cache[Get1DIndexFrom2D(P[i].zw + int2(1, 0), CacheWidth)];
         float3 T_W = Cache[Get1DIndexFrom2D(P[i].zw + int2(-1, 0), CacheWidth)];
         float3 T = Cache[Get1DIndexFrom2D(P[i].zw, CacheWidth)];

         // Get dynamic data
         float2 UV = WarpTex + (float2(P[i].xy) * PixelSize);
         bool CenterFetch = (P[i].x == 0) && (P[i].y == 0);
         float3 I = CenterFetch
            ? I_C
            : GetPlanesYUV(SampleI, UV);

         // Calculate bilateral weighting
         float Weight = CenterFetch
            ? 1.0
            : GetDiceIndex(TT_II, T_C, T, I_C, I);

         // Accumulate weight
         WSum += Weight;

         // Immediately calculate spatial gradients
         float3 Ix = (T_W - T_E) * 0.5;
         float3 Iy = (T_N - T_S) * 0.5;
         A[0] += (dot(Ix, Ix) * Weight);
         A[1] += (dot(Iy, Iy) * Weight);
         A[2] += (dot(Ix, Iy) * Weight);

         float3 It = I - T;
         B[0] += (dot(Ix, It) * Weight);
         B[1] += (dot(Iy, It) * Weight);
      }

      // Normalized weighted variables
      WSum = 1.0 / WSum;
      A *= WSum;
      B *= WSum;

      /*
         Calculate Lucas-Kanade matrix
         ---
         [ Ix^2/D -IxIy/D] = [-IxIt]
         [-IxIy/D  Iy^2/D]   [-IyIt]

         [ A[0] -A[2]] = [-B[0]]
         [-A[2]  A[1]]   [-B[1]]
      */

      /*
         ANISOTROPY FACTOR
         -----------------

         1. Mathematical Derivation:

            We start with the Normalized Anisotropy metric 'S' and the Trace-scaled
            damping factor 'Lambda':

               S = 1.0 - (4.0 * Dt) / (Tr * Tr)
               Lambda = Tr * S

            Substituting S into Lambda and applying the distributive property:

               Lambda = Tr * (1.0 - (4.0 * Dt) / (Tr * Tr))
               Lambda = Tr - (Tr * (4.0 * Dt) / (Tr * Tr))
               Lambda = Tr - ((4.0 * Dt) / Tr)

         This algebraic simplification cancels out one 'Tr' term.

         2. Why We Scale by the Trace (Tr):

            Scaling Lambda by the Trace (total local gradient energy, Tr = Ix^2 + Iy^2) makes the damping factor scale-invariant / contrast-invariant.

            Is this very prevalent if you apply a constant to the diagonals, but the influences of A00 & A11 become too weak in low contrast areas (low gradients scale) and high contrast areas (high gradient scale)

            If image contrast changes by a factor 'c' (I' = c * I):

               * Structure Tensor elements scale by c^2.
               * Trace scales by c^2 (Tr' = c^2 * Tr).
               * Determinant scales by c^4 (Dt' = c^4 * Dt).

            Without Trace-scaling (using a fixed static constant Lambda):

               * High contrast: Lambda is too small for matrix inversion.
               * Low contrast: Lambda dominates the matrix relative to the scale of the gradients.

            With Trace-scaling:

               * Lambda' = c^2 * Lambda.
               * Lambda grows and shrinks in exact 1:1 proportion with the Hessian's diagonal elements (A00, A11), preserving identical regularized flow vectors regardless of brightness or exposure changes.
      */

      float Tr = A[0] + A[1];
      float XY = A[2] * A[2];
      float Dt = (A[0] * A[1]) - XY;
      float Tr_Rcp = 1.0 / Tr;

      float Lambda = isinf(Tr_Rcp)
         ? 0.0
         : max(0.0, Tr - ((4.0 * Dt) * Tr_Rcp));

      // Regularized Hessian Diagonal
      float A00 = A[0] + Lambda;
      float A11 = A[1] + Lambda;

      // Invert Regularized Hessian
      float Dt_Rcp = 1.0 / ((A00 * A11) - XY);

      float2 Flow = float2(
         (A[2] * B[1]) - (A11 * B[0]),
         (A[2] * B[0]) - (A00 * B[1])
      );

      Flow = isinf(abs(Dt_Rcp))
         ? 0.0
         : Flow * Dt_Rcp;

      // Propagate normalized motion vectors in Norm Range
      Vectors += (Flow * PixelSize);

      // Clamp motion vectors to restrict range to valid lengths
      Vectors = clamp(Vectors, -1.0, 1.0);

      // Encode motion vectors to FP16 format
      return SNORMtoFP16_FLT2(Vectors);
   }

Technical Details
-----------------

This section documents key implementation choices critical for understanding and using the HLSL code.

FP16 Motion Vector Storage
^^^^^^^^^^^^^^^^^^^^^^^^^^

The algorithm encodes motion vectors using **FP16 (16-bit half-precision floating-point)** format:

* Memory efficiency: FP16 uses half the memory of 32-bit floats
* GPU compatibility: FP16 is natively supported on modern GPUs
* Sufficient range and precision for normalized motion vectors
* Stored in [-1.0, 1.0) range using SNORM encoding

Conversion helpers:

.. describe:: FP16toSNORM_FLT2()

   Converts from FP16 range to normalized [-1.0, 1.0) range

.. describe:: SNORMtoFP16_FLT2()

   Converts back to FP16 for storage

.. describe:: GetFP16Max()

   Returns the maximum FP16 value for normalization

Normalized Displacement Output
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The algorithm outputs **normalized displacements** rather than pixel displacements:

* Motion vectors are normalized to the [-1.0, 1.0) range
* The ``PixelSize`` parameter scales normalized vectors to actual pixel displacements
* This normalization makes the algorithm resolution-independent and numerically stable

Texture Cache and Fetch Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The implementation uses a **5x5 texture cache** with a **3x3 processing grid**:

* **5x5 Cache**: Samples a 5x5 neighborhood around each pixel (25 total samples)
* **3x3 Processing Grid**: Uses 9 sample points arranged in a cross pattern plus center
* **Fetch Pattern**: The 9 points cover edge, cardinal, and center regions
* **Cache Structure**: Stored in a 1D array for efficient GPU access
* **Indexing**: Uses ``Get1DIndexFrom2D()`` helper function for cache access

This pattern balances computational cost with motion estimation accuracy.

Inverse Warping Approach
^^^^^^^^^^^^^^^^^^^^^^^^

The implementation uses **inverse warping** as part of the Gauss-Newton optimization:

.. math::

   \text{WarpTex} = \text{MainTex} - 0.5 - \text{Vectors}

.. describe:: MainTex

   The current pixel coordinate in [0, 1) range

.. describe:: Vectors

   Contains the current motion estimate

The warp pulls coordinates into [-0.5, 0.5) range, applies the inverse motion, then pushes back to [0, 1) range.

This approach is more numerically stable than forward warping and aligns with the inverse compositional formulation.

Central Differences for Gradient Calculation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Spatial gradients use **central differences** for improved accuracy:

.. math::

   I_x = (I_{west} - I_{east}) \times 0.5 \\
   I_y = (I_{north} - I_{south}) \times 0.5

where the 0.5 factor normalizes the gradient magnitude. This provides second-order accuracy compared to forward/backward differences.

References
----------

* Baker, S., & Matthews, I. (2004). Lucas-kanade 20 years on: A unifying framework. *International journal of computer vision*, 56, 221-255.
* C\. Gatta, M. Sbert, and M. A. Rodrigues. (2004). "Dice Coefficient", in *Encyclopedia of Medical Imaging*.
* Rojas, R. (2010). Lucas-kanade in a nutshell. Freie Universit at Berlinn, Dept. of Computer Science, Tech. Rep.
* Titkov, V. V., Panin, S. V., Lyubutin, P. S., Chemezov, V. O., & Eremin, A. V. (2017). Application of Lucas-Kanade algorithm with weight coefficient bilateral filtration for the digital image correlation method. *IOP Conference Series: Materials Science and Engineering*, 177, 012039. https://doi.org/10.1088/1757-899X/177/1/012039
* Wikipedia contributors. (2024, May 15). Lucas-Kanade method. In *Wikipedia, The Free Encyclopedia*. Retrieved 18:46, July 3, 2025, from https://en.wikipedia.org/w/index.php?title=Lucas%E2%80%93Kanade_method&oldid=1223913530
