
Adaptive-Weighted Lucas-Kanade Optical Flow on the GPU
======================================================

An optical flow algorithm estimates motion between consecutive video frames. Optical flow is crucial in object detection, object recognition, motion estimation, video compression, and video effects.

This document covers an HLSL implementation of the Lucas-Kanade optical flow algorithm with adaptive weighting for improved robustness.

Overview
--------

This document provides a comprehensive guide to the Adaptive-Weighted Lucas-Kanade optical flow algorithm implemented on the GPU using HLSL. The guide is organized into four main sections:

#. **Theoretical Foundations**: Covers the mathematical principles underlying optical flow, including the Brightness Constancy Assumption, Optical Flow Equation, and the Aperture Problem
#. **The Lucas-Kanade Method**: Explains the standard Lucas-Kanade approach and its Gauss-Newton variant, along with the least-squares derivation
#. **Advanced Techniques**: Details enhancement techniques such as bilateral weighting, anisotropy factor regularization, and pyramid approaches
#. **Implementation**: Provides the complete HLSL source code and technical details about the implementation choices

The document balances theoretical explanations with practical implementation guidance, making it suitable for both researchers and developers working with optical flow algorithms.

Theoretical Foundations
-----------------------

The theoretical foundations of optical flow provide the mathematical framework for understanding and implementing motion estimation algorithms. This section covers the core principles that make optical flow algorithms possible.

The Brightness Constancy Assumption
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When tracking an object visually, we rely on assumptions about how its appearance changes. For example, we can infer that a red dot has moved if we observe it maintaining its red color but appearing in a different location than it did a moment ago.

Accurate motion estimation in video relies on two fundamental assumptions:

#. The intensity (brightness and color) of an object's movement in two consecutive images remains *approximately constant*.
#. The movement of objects between two images is *small*.

These assumptions form the basis of the **Brightness Constancy Assumption**.

.. math::

   I(x, y, t) = I(x + u, y + v, t + 1)

.. note::

   **The Brightness Constancy Assumption has a limitation**: This assumption holds best for objects whose appearance does not significantly change between frames. For instance, it would struggle with a ball that constantly changes color or an object moving into shadow or direct light.

The Optical Flow Equation
^^^^^^^^^^^^^^^^^^^^^^^^^

The Brightness Constancy Assumption states:

.. math::

   I(x, y, t) = I(x + u, y + v, t + 1)

This equation states that the intensity at a point :math:`(x, y)` in the previous image :math:`I` at time :math:`t` equals the intensity of the *same point* at a new position :math:`(x + u, y + v)` in the current image at time :math:`t + 1`. Our goal is to solve for :math:`u` and :math:`v`, the horizontal and vertical components of the optical flow vector.

To achieve this, we need a mathematical way to approximate the rate of change of image intensity. This is where derivatives and the Taylor series expansion become crucial.

We apply a first-order Taylor series expansion to the right-hand side of the Brightness Constancy Assumption around the point :math:`(x, y, t)`:

.. math::

   I(x + u, y + v, t + 1) \approx I(x, y, t) + \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

Substituting this approximation back into the Brightness Constancy Assumption and simplifying:

.. math::

   I(x, y, t) &\approx I(x, y, t) + \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}\\
   0 &\approx \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

This is the **Optical Flow Equation**. Rearranging it to isolate the temporal change:

.. math::

   \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v \approx -\frac{\partial I}{\partial t}

This represents the spatial gradient (how brightness changes horizontally and vertically):

.. math::

   \frac{\partial I}{\partial x}, \frac{\partial I}{\partial y}

And the temporal gradient (how brightness changes over time at a fixed location):

.. math::

   \frac{\partial I}{\partial t}

Our objective is to solve for :math:`u` and :math:`v`, the horizontal and vertical components of the optical flow vector.

.. note::

   We use a first-order Taylor series expansion because the "small movement" assumption means that the changes regarding :math:`x`, :math:`y`, :math:`t` are small. This allows us to ignore higher-order terms in the expansion, which simplifies the math significantly while still providing a good approximation.

The Aperture Problem - In Practice
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's a practical demonstration of the Aperture Problem:

#. Get a string long enough that you cannot see its ends when viewing it through a small, fixed opening (an "aperture").
#. Position the string behind the opening.
#. Angle the string at 45-degrees.
#. Now, slide the string through the opening in the following ways, ensuring its ends remain outside your view through the hole:

   * **Horizontally** slide the string across the opening.
   * **Vertically** slide the string across the opening.
   * **Diagonally** slide the string across the opening.

Did you see a difference in motion when sliding the string horizontally, vertically, or diagonally? Probably not, unless you can see the entire string within the opening.

**The Problem**: Your limited perception through the small aperture causes you to observe the string appearing to "move the same way" (only perpendicular to its orientation), regardless of its actual global movement direction. You cannot disambiguate its true 2D motion.

The Aperture Problem - In Mathematics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the Optical Flow Equation:

.. math::

   \frac{\partial I}{\partial x} u + \frac{\partial I}{\partial y} v \approx -\frac{\partial I}{\partial t}

Imagine you're in a math class, and your teacher asks the class to solve the following single linear equation for unknowns :math:`u` and :math:`v`:

.. math::

   3u + 4v = 0

Possible solutions the class might propose include:

.. math::

   u = -4, v = 3 \\
   u = 4, v = -3 \\
   u = 0, v = 0

This demonstrates that for a single pixel (which acts as a tiny aperture), the optical flow equation provides only one equation with two unknowns :math:`u` and :math:`v`. Consequently, there are infinitely many pairs of :math:`(u, v)` that satisfy the equation. If you plot these solutions on a graph, they all lie on a single line, meaning the true direction of motion is ambiguous. Only the component of motion perpendicular to the image gradient can be determined.

The Lucas-Kanade Approach to The Aperture Problem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Lucas-Kanade method is a **local** technique designed to overcome the aperture problem by solving a system of optical flow equations within a small spatial window or neighborhood.

To estimate the local image flow at a given point, the Lucas-Kanade method employs a least-squares approach. This method solves an overdetermined system of linear equations, where each pixel within the chosen window contributes an optical flow equation.

Least-Squares Derivation
^^^^^^^^^^^^^^^^^^^^^^^^

This is the initial system of linear equations in the form :math:`A \boldsymbol{x} = \boldsymbol{b}`.

.. math::

   \begin{bmatrix}
   I_{x_{1}} & I_{y_{1}} \\
   I_{x_{2}} & I_{y_{2}} \\
   I_{x_{3}} & I_{y_{3}}
   \end{bmatrix}
   \begin{bmatrix}
   u \\
   v
   \end{bmatrix} =
   \begin{bmatrix}
   -I_{t_{1}} \\
   -I_{t_{2}} \\
   -I_{t_{3}}
   \end{bmatrix}

To find the least-squares solution, we multiply both sides by the transpose of the matrix, :math:`A^T`.

.. math::

   \begin{bmatrix}
   I_{x_{1}} & I_{x_{2}} & I_{x_{3}} \\
   I_{y_{1}} & I_{y_{2}} & I_{y_{3}}
   \end{bmatrix}
   \begin{bmatrix}
   I_{x_{1}} & I_{y_{1}} \\
   I_{x_{2}} & I_{y_{2}} \\
   I_{x_{3}} & I_{y_{3}}
   \end{bmatrix}
   \begin{bmatrix}
   u \\
   v
   \end{bmatrix} =
   \begin{bmatrix}
   I_{x_{1}} & I_{x_{2}} & I_{x_{3}} \\
   I_{y_{1}} & I_{y_{2}} & I_{y_{3}}
   \end{bmatrix}
   \begin{bmatrix}
   -I_{t_{1}} \\
   -I_{t_{2}} \\
   -I_{t_{3}}
   \end{bmatrix}

The result of the matrix multiplication is expressed in summation form:

.. math::

   \begin{bmatrix}
   \sum I_{x_{i}}^{2} & \sum I_{x_{i}}I_{y_{i}} \\
   \sum I_{x_{i}}I_{y_{i}} & \sum I_{y_{i}}^{2}
   \end{bmatrix}
   \begin{bmatrix}
   u \\
   v
   \end{bmatrix} =
   \begin{bmatrix}
   \sum -I_{t_{i}}I_{x_{i}} \\
   \sum -I_{t_{i}}I_{y_{i}}
   \end{bmatrix}

We now multiply both sides by the inverse of the matrix on the left, :math:`(A^T A)^{-1}`, to isolate the :math:`\begin{bmatrix} u \\ v \end{bmatrix}` vector:

.. math::

   \begin{bmatrix}
   \sum I_{x_{i}}^{2} & \sum I_{x_{i}}I_{y_{i}} \\
   \sum I_{x_{i}}I_{y_{i}} & \sum I_{y_{i}}^{2}
   \end{bmatrix}^{-1}
   \begin{bmatrix}
   \sum I_{x_{i}}^{2} & \sum I_{x_{i}}I_{y_{i}} \\
   \sum I_{x_{i}}I_{y_{i}} & \sum I_{y_{i}}^{2}
   \end{bmatrix}
   \begin{bmatrix}
   u \\
   v
   \end{bmatrix} =
   \begin{bmatrix}
   \sum I_{x_{i}}^{2} & \sum I_{x_{i}}I_{y_{i}} \\
   \sum I_{x_{i}}I_{y_{i}} & \sum I_{y_{i}}^{2}
   \end{bmatrix}^{-1}
   \begin{bmatrix}
   \sum -I_{t_{i}}I_{x_{i}} \\
   \sum -I_{t_{i}}I_{y_{i}}
   \end{bmatrix}

The final step is the solution for the vector :math:`\begin{bmatrix} u \\ v \end{bmatrix}`:

.. math::

   \begin{bmatrix}
   u \\
   v
   \end{bmatrix} =
   \begin{bmatrix}
   \sum I_{x_{i}}^{2} & \sum I_{x_{i}}I_{y_{i}} \\
   \sum I_{x_{i}}I_{y_{i}} & \sum I_{y_{i}}^{2}
   \end{bmatrix}^{-1}
   \begin{bmatrix}
   \sum -I_{t_{i}}I_{x_{i}} \\
   \sum -I_{t_{i}}I_{y_{i}}
   \end{bmatrix}

Using Bilateral Weights
-----------------------

The standard Lucas-Kanade method treats all pixels in the neighborhood equally. However, this can lead to inaccuracies near edges or in the presence of noise, where some pixels in the window may not belong to the same moving object.

To improve robustness, bilateral weighting assigns a weight to each pixel's contribution based on its similarity to the center pixel. This implementation uses the **Dice similarity metric**, which combines angular alignment and relative scale into a unified similarity score.

This version uses a pre-computed sum of squared magnitudes (E) for efficiency:

.. math::

   N &= \mathrm{dot}(T_r, T_s) + \mathrm{dot}(I_r, I_s)\\
   D &= \mathrm{dot}(T_s, T_s) + \mathrm{dot}(I_s, I_s) + E

where E is typically computed as :math:`E = \mathrm{dot}(T_r, T_r) + \mathrm{dot}(I_r, I_r)`.

The Dice similarity metric maps the similarity to the range [0.0, 1.0], where 1.0 indicates perfect similarity and 0.0 indicates no similarity. The implementation uses the 3D version of the function for YUV color similarity.

The similarity is computed as:

.. math::

   \mathrm{Similarity} = \left(\frac{N}{D}\right) + 0.5

where the result is clamped to the range [0.0, 1.0] using ``saturate()``.

.. important:: Bilateral Weighting Implementation Details

   * The center pixel always receives a weight of 1.0 (maximum similarity to itself)
   * The Dice similarity metric determines each pixel's contribution based on color and intensity similarity to the center pixel
   * Weights are normalized by dividing by the sum of all weights (WSum)
   * The normalized weights are applied to the spatial and temporal gradients before accumulating
   * This approach gives more influence to pixels that are similar to the center pixel in both color and intensity

These weights are then incorporated into the least-squares summation, performing a weighted least-squares estimation.

.. note::

   The Dice index provides a normalized measure of similarity between two vectors. The addition of 0.5 ensures the result falls within the [0.0, 1.0] range, where 1.0 represents perfect similarity and 0.0 represents no similarity.

Advanced Techniques
-------------------

Advanced techniques enhance the basic Lucas-Kanade algorithm with improved robustness, stability, and accuracy for challenging scenarios.

Using Pyramids
^^^^^^^^^^^^^^

.. note:: Implementation Note

   The pyramid approach described in this section is a well-established extension to Lucas-Kanade for handling large motions. However, the code implementation provided in this document focuses specifically on the **single-level Gauss-Newton Lucas-Kanade algorithm** with anisotropy factor regularization. The pyramid extension is not included in the provided code but can be implemented by wrapping the ``GetLucasKanade`` function in a multi-resolution framework.

The Lucas-Kanade method, while effective for small displacements, becomes less accurate for large motions. This is because large movements violate the "small movement" assumption inherent in the first-order Taylor expansion and the brightness constancy assumption. To handle larger motions while maintaining efficiency and adherence to assumptions, a hierarchical, or "pyramid," approach is commonly used.

This approach ensures:

* It does not break the **brightness constancy** assumption, as motion is incrementally estimated at different scales.
* It handles cases where the actual movement between two images is significant.
* It facilitates fast computation by starting with coarse motion estimates at lower resolutions.
* It covers motion in areas larger than a 3x3 window by propagating estimates across pyramid levels.

The pyramid Lucas-Kanade algorithm consists of the following general steps:

#. Create an image pyramid for the current frame and previous frame.
#. Initialize the motion vector at the smallest pyramid level to **0.0** or a previous estimate.
#. Compute optical flow iteratively from the smallest pyramid level to the largest level. At each level, the flow from the smaller level is used to "warp" the image, reducing the remaining displacement, and then a refinement is calculated.
#. Cache the current frame (or its pyramid) for use as the "previous frame" in the next optical flow calculation.
#. Optionally, filter the computed optical flow vectors to remove noise or outliers.

Inverse Warping Approach
^^^^^^^^^^^^^^^^^^^^^^^^

The implementation uses **inverse warping** as part of the Gauss-Newton optimization:

.. math::

   \text{WarpTex} = \text{MainTex} - 0.5 - \text{Vectors}

Where:

* ``MainTex`` is the current pixel coordinate in [0, 1) range
* ``Vectors`` contains the current motion estimate
* The warp pulls coordinates into [-0.5, 0.5) range, applies the inverse motion, then pushes back to [0, 1) range

This approach is more numerically stable than forward warping and aligns with the inverse compositional formulation of the Gauss-Newton method.

Central Differences for Gradient Calculation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Spatial gradients are computed using **central differences** for improved accuracy:

.. math::

   I_x = (I_{west} - I_{east}) \times 0.5
   I_y = (I_{north} - I_{south}) \times 0.5

Where:

* :math:`I_{west}`, :math:`I_{east}`, :math:`I_{north}`, :math:`I_{south}` are pixel values from the 5x5 cache
* The 0.5 factor normalizes the gradient magnitude

This method provides second-order accuracy compared to forward/backward differences, which are only first-order accurate.

Anisotropy Factor and Regularization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To ensure numerical stability and improve accuracy, especially in low-texture regions or areas with minimal gradient information, this implementation incorporates an **anisotropy factor with trace-scaled regularization**. This sophisticated regularization technique addresses two key challenges:

#. **Numerical Stability**: Prevents matrix inversion failures in regions with uniform texture
#. **Scale Invariance**: Maintains consistent performance across varying image contrast levels

The regularization works by computing a damping factor :math:`\Lambda` that is added to the diagonal elements of the structure tensor. The key innovation is **trace-scaling**, where the damping factor scales proportionally with the trace of the structure tensor (total local gradient energy).

Mathematically, the regularization is computed as:

.. math::

   \Lambda = \begin{cases}
   0 & \text{if } Tr > 0 \text{ (no regularization when gradients exist)} \\
   Tr - \frac{4Dt}{Tr} & \text{if } Tr \leq 0 \text{ (apply regularization)}
   \end{cases}

Where:

* :math:`Tr = A[0] + A[1]` is the trace (sum of diagonal elements)
* :math:`Dt = (A[0] \times A[1]) - (A[2] \times A[2])` is the determinant
* :math:`A[0] = \sum I_x^2`, :math:`A[1] = \sum I_y^2`, :math:`A[2] = \sum I_x I_y` are structure tensor elements

.. important:: Why Trace-Scaling Matters

   Without trace-scaling, regularization would be contrast-dependent:

   * **High-contrast regions**: Lambda would be too small, leading to instability
   * **Low-contrast regions**: Lambda would dominate, suppressing valid motion signals

   With trace-scaling, Lambda grows and shrinks in exact proportion to the gradient magnitudes, preserving identical flow vectors regardless of brightness or exposure changes. This makes the algorithm robust across varying lighting conditions and image qualities.

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

This regularization is applied before inverting the structure tensor to solve for the optical flow vector, ensuring robust and stable solutions even in challenging conditions.

Implementation (Source Code)
----------------------------

The implementation section provides the complete HLSL source code and technical details about the implementation choices made in this optical flow algorithm.

.. note::

   The code contains **generic** functions, so you may need to change some parts of the code to make it compatible with your setup.

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
      D = (D > 0.0) ? 1.0 / D : 0.5;
      return saturate((N * D) + 0.5);
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
      Lucas-Kanade optical flow with bilinear fetches. The algorithm is modified to not output in pixels, but normalized displacements.

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

      // Get center magnitudes.
      float TT_II = dot(T_C, T_C) + dot(I_C, I_C);

      [unroll]
      for (int i = 0; i < FetchGridSize; i++)
      {
         // Get cached data.
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

            Is this very prevalent if you apply a constant to the diagonals, but the influences of A00 & A11 become too weak in low contrast areas (low gradients scale) and high contrast areas (high gradient scale).

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

      float Lambda = (Tr > 0.0)
         ? max(GetFP16Min(), Tr - ((4.0 * Dt) / Tr))
         : 0.0;

      // Regularized Hessian Diagonal
      float A00 = A[0] + Lambda;
      float A11 = A[1] + Lambda;

      // Invert Regularized Hessian
      float Dt_1 = (A00 * A11) - XY;

      float2 Flow = float2(
         A[2] * B[1] - A11 * B[0],
         A[2] * B[0] - A00 * B[1]
      );

      Flow = (abs(Dt_1) > 0.0) ? Flow / Dt_1 : 0.0;

      // Propagate normalized motion vectors in Norm Range
      Vectors += (Flow * PixelSize);

      // Clamp motion vectors to restrict range to valid lengths
      Vectors = clamp(Vectors, -1.0, 1.0);

      // Encode motion vectors to FP16 format
      return SNORMtoFP16_FLT2(Vectors);
   }

Implementation Details
----------------------

This section documents key implementation choices and technical details that are critical for understanding and using the provided HLSL code.

FP16 Motion Vector Storage
^^^^^^^^^^^^^^^^^^^^^^^^^^

The algorithm encodes motion vectors using **FP16 (16-bit half-precision floating-point)** format rather than standard 32-bit floats. This choice provides several benefits:

* **Memory Efficiency**: FP16 uses half the memory of 32-bit floats, crucial for GPU implementations with many motion vectors
* **GPU Compatibility**: FP16 is natively supported on modern GPUs and shaders
* **Range and Precision**: The format provides sufficient range (-65504 to 65504) and reasonable precision for normalized motion vectors
* **Storage Format**: Motion vectors are stored in the range [-1.0, 1.0) using SNORM encoding, then converted to FP16

The conversion process uses the following helper functions:

* ``FP16toSNORM_FLT2()``: Converts from FP16 range to normalized [-1.0, 1.0) range
* ``SNORMtoFP16_FLT2()``: Converts back to FP16 for storage
* ``GetFP16Max()``: Returns the maximum FP16 value for normalization

Normalized Displacement Output
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The algorithm outputs **normalized displacements** rather than pixel displacements:

* Motion vectors are normalized to the [-1.0, 1.0) range
* The ``PixelSize`` parameter scales the normalized vectors to actual pixel displacements
* This normalization makes the algorithm resolution-independent and more numerically stable

Texture Cache and Fetch Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The implementation uses a **5x5 texture cache** with a **3x3 processing grid** for efficiency:

* **5x5 Cache**: Samples a 5x5 neighborhood around each pixel (25 total samples)
* **3x3 Processing Grid**: Uses 9 sample points arranged in a cross pattern plus center
* **Fetch Pattern**: The 9 points are strategically positioned to cover edge, cardinal, and center regions
* **Cache Structure**: The cache is stored in a 1D array for efficient GPU access
* **Indexing**: Uses ``Get1DIndexFrom2D()`` helper function for cache access

This pattern provides a good balance between computational cost and motion estimation accuracy, capturing motion information in multiple directions.

References
----------

* Baker, S., & Matthews, I. (2004). Lucas-kanade 20 years on: A unifying framework. *International journal of computer vision*, 56, 221-255.
* C. Gatta, M. Sbert, and M. A. Rodrigues. (2004). "Dice Coefficient", in *Encyclopedia of Medical Imaging*.
* Rojas, R. (2010). Lucas-kanade in a nutshell. Freie Universit at Berlinn, Dept. of Computer Science, Tech. Rep.
* Titkov, V. V., Panin, S. V., Lyubutin, P. S., Chemezov, V. O., & Eremin, A. V. (2017). Application of Lucas-Kanade algorithm with weight coefficient bilateral filtration for the digital image correlation method. *IOP Conference Series: Materials Science and Engineering*, 177, 012039. https://doi.org/10.1088/1757-899X/177/1/012039
* Wikipedia contributors. (2024, May 15). Lucas-Kanade method. In *Wikipedia, The Free Encyclopedia*. Retrieved 18:46, July 3, 2025, from https://en.wikipedia.org/w/index.php?title=Lucas%E2%80%93Kanade_method&oldid=1223913530
