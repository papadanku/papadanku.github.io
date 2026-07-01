
Adaptive-Weighted Lucas-Kanade Optical Flow on the GPU
======================================================

An optical flow algorithm estimates motion between consecutive video frames. Optical flow is crucial in object detection, object recognition, motion estimation, video compression, and video effects.

This post covers an HLSL implementation of the Lucas-Kanade optical flow algorithm.

The Brightness Constancy Assumption
-----------------------------------

When we use our eyes to track an object, we make assumptions to determine if an object has moved. For example, we can infer that a red dot has moved if we observe it maintaining its red color but appearing in a different location than it did a moment ago.

Accurate motion estimation in video relies on fundamental assumptions:

#. The intensity \(brightness and color\) of an object's movement in two consecutive images remains *approximately constant*.
#. The movement of objects between two images is *small*.

These assumptions form the basis of the **Brightness Constancy Assumption**.

.. math:: I(x, y, t) = I(x + u, y + v, t + 1)

.. note::

   **The Brightness Constancy Assumption has a limitation**: This assumption holds best for objects whose appearance does not significantly change between frames. For instance, it would struggle with a ball that constantly changes color or an object moving into shadow or direct light.

The Optical Flow Equation
-------------------------

Let's revisit the Brightness Constancy Assumption:

.. math:: I(x, y, t) = I(x + u, y + v, t + 1)

From this direct equality, it's not obvious how to create a formula for optical flow, as it states that the intensity at a point :math:`(x, y)` in the previous image :math:`I` at time :math:`t` is equal to the intensity of the *same point* at a new position :math:`(x + u, y + v)` in the current image at time :math:`t + 1`. Our goal is to find :math:`u` and :math:`v`.

To achieve this, we need a mathematical way to approximate the rate of change of image intensity from :math:`I(x, y, t)` to :math:`I(x + u, y + v, t + 1)`. This is where derivatives and the Taylor series expansion become crucial.

We apply a first-order Taylor series expansion to the right-hand side of the Brightness Constancy Assumption, around the point :math:`(x, y, t)`:

.. math::

   I(x + u, y + v, t + 1) \approx I(x, y, t) + \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

Substituting this approximation back into the Brightness Constancy Assumption and simplifying:

.. math::

   I(x, y, t) \approx I(x, y, t) + \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}\\
   0 \approx \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

This is the **Optical Flow Equation**. Rearranging it to isolate the temporal change:

.. math::

   \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v \approx -\frac{\partial I}{\partial t}

This is the spatial gradient \(how brightness changes horizontally and vertically\):

.. math:: \frac{\partial I}{\partial x}, \frac{\partial I}{\partial y}

This is the temporal gradient \(how brightness changes over time at a fixed location\):

.. math:: \frac{\partial I}{\partial t}

Our objective is to solve for :math:`u` and :math:`v`, the horizontal and vertical components of the optical flow vector.

.. note::

   We use a first-order Taylor series expansion because the "small movement" assumption means that the changes regarding :math:`x`, :math:`y`, :math:`z` are small. This allows us to ignore higher-order terms in the expansion, which simplifies the math significantly while still providing a good approximation.

The Aperture Problem - In Practice
----------------------------------

Here's a practical demonstration of the Aperture Problem.

#. Get a string long enough that you cannot see its ends when viewing it through a small, fixed opening \(an "aperture"\).
#. Position the string behind the opening.
#. Angle the string at 45-degrees.
#. Now, slide the string through the opening in the following ways, ensuring its ends remain outside your view through the hole:

   - **Horizontally** slide the string across the opening.
   - **Vertically** slide the string across the opening.
   - **Diagonally** slide the string across the opening.

Did you see a difference in motion when sliding the string horizontally, vertically, or diagonally? Probably not, unless you can see the entire string within the opening.

**The Problem**: Your limited perception through the small aperture causes you to observe the string appearing to "move the same way" \(only perpendicular to its orientation\), regardless of its actual global movement direction. You cannot disambiguate its true 2D motion.

Let's examine the mathematical version of this problem.

The Aperture Problem - In Mathematics
-------------------------------------

Consider the Optical Flow Equation:

.. math::

   \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v \approx -\frac{\partial I}{\partial t}

Imagine you're back in your underfunded school's math class, and your teacher asks the class to solve the following single linear equation for unknowns :math:`u` and :math:`v`:

.. math::

   3u + 4v = 0

Possible solutions the class might propose include:

.. math::

   u = -4, v = 3 \\
   u = 4, v = -3 \\
   u = 0, v = 0

This demonstrates that for a single pixel \(which acts as a tiny aperture\), the optical flow equation provides only one equation on two unknowns :math:`u` and :math:`v`. Consequently, there are infinitely many pairs of :math:`(u, v)` that satisfy the equation. If you plot these solutions on a graph, they all lie on a single line, meaning the true direction of motion is ambiguous - only the component of motion perpendicular to the image gradient can be determined.

The Lucas-Kanade Approach to The Aperture Problem
-------------------------------------------------

The Lucas-Kanade method is a **local** technique designed to overcome the aperture problem by solving a system of optical flow equations within a small spatial window or neighborhood.

To estimate the local image flow at a given point, the Lucas-Kanade method employs a least-squares approach. This method solves an overdetermined system of linear equations, where each pixel within the chosen window contributes an optical flow equation.

The standard Lucas-Kanade algorithm typically solves these systems of equations within a 3x3 window, as this size often provides a good balance, effectively considering motion components in various directions.

Least-Squares Derivation
^^^^^^^^^^^^^^^^^^^^^^^^

This is the initial system of linear equations in the form :math:`A \mathbf{x} = \mathbf{b}`.

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

The result of the matrix multiplication is expressed in summation form.

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

We now multiply both sides by the inverse of the matrix on the left, :math:`(A^T A)^{-1}`, to isolate the :math:`\begin{bmatrix} u \\ v \end{bmatrix}` vector.

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

The final step is the solution for the vector :math:`\begin{bmatrix} u \\ v \end{bmatrix}`.

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

To improve robustness, bilateral weighting assigns a weight to each pixel's contribution based on its spatial and intensity distance from the center pixel.

The weight :math:`W` is the product of a spatial weight and a range weight:

.. math::

   W = W_{spatial} \cdot W_{range}

The spatial weight ensures that pixels closer to the center have more influence:

.. math::

   W_{spatial} = 2^{-(|\Delta x| + |\Delta y|)}

The range weight reduces the influence of pixels with intensity differences, which indicate an edge or a different object:

.. math::

   W_{range} = \frac{1}{1 + \|I_{pixel} - I_{center}\|^2}

These weights are then incorporated into the least-squares summation, performing a weighted least-squares estimation.

Using Pyramids
--------------

The Lucas-Kanade method, while effective for small displacements, becomes less accurate for large motions. This is because large movements violate the "small movement" assumption inherent in the first-order Taylor expansion and the brightness constancy assumption. To handle larger motions while maintaining efficiency and adherence to assumptions, a hierarchical, or "pyramid," approach is used:

This approach ensures:

- It does not break the **brightness constancy** assumption, as motion is incrementally estimated  at different scales.
- It handles cases where the actual movement between two images is significant.
- It facilitates fast computation by starting with coarse motion estimates at lower resolutions.
- It covers motion in areas larger than a 3x3 window by propagating estimates across pyramid levels.

The pyramid Lucas-Kanade algorithm consists of the following general steps:

#. Create an image pyramid for the current frame and previous frame.
#. Initialize the motion vector at the smallest pyramid level to **0.0** or a previous estimate.
#. Compute optical flow iteratively from the smallest pyramid level to the largest level. At each level, the flow from the smaller level is used to "warp" the image, reducing the remaining displacement, and then a refinement is calculated.
#. Cache the current frame \(or its pyramid\) for use as the "previous frame" in the next optical flow calculation.
#. Optionally, filter the computed optical flow vectors to remove noise or outliers.

Source Code
-----------

.. note::

   The code contains **generic** functions, so you may need to change some parts of the code so it is compatible with your setup.

.. code-block:: hlsl
   :caption: Converting from 2D Grid Position to 1D Index

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

.. code-block:: hlsl
   :caption: Data Encoding & Decoding

   // Get the Half format distribution of bits
   // Sign Exponent Significand
   // x    xxxxx    xxxxxxxxxx
   float CalculateFLT16(int Sign, int Exponent, int Significand)
   {
      const int Bias = -15;
      const int MaxExponent = (Exponent - exp2(1)) + Bias;
      const int MaxSignificand = 1 + ((Significand - 1) / Significand);

      return (float)pow(-1, Sign) * (float)exp2(MaxExponent) * (float)MaxSignificand;
   }

   float GetFLT16Max()
   {
      /*
         Sign Exponent Significand
         ---- -------- -----------
         0    11110    1111111111
      */
      return CalculateFLT16(0, exp2(5), exp2(10));
   }

   // [-HalfMax, HalfMax) -> [-1.0, 1.0)
   float2 FLT16toSNORM_FLT2(float2 Value)
   {
      return Value / GetFLT16Max();
   }

   // [-1.0, 1.0) -> [-HalfMax, HalfMax)
   float2 SNORMtoFLT16_FLT2(float2 Value)
   {
      return Value * GetFLT16Max();
   }

.. code-block:: hlsl
   :caption: SRGB to YUV

   /*
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

   float3 GetPlanesYUV(sampler2D Image, float2 Tex)
   {
      float3 Color = tex2D(Image, Tex).rgb;
      Color = SRGBtoYUV444(Color);
      return Color;
   }

.. code-block:: hlsl
   :caption: Adaptive-Weighted Lucas-Kanade Optical Flow

   /*
      Lucas-Kanade optical flow with bilinear fetches. The algorithm is motified to not output in pixels, but normalized displacements.

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
      float2 MainTex, // [0, 1)
      float2 Vectors, // [-fp16max, +fp16max)
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

      const float3 SWeights = exp2(-float3(0.0, 1.0, 2.0));

      // Decode from FLT16
      Vectors = clamp(FLT16toSNORM_FLT2(Vectors), -1.0, 1.0);

      // Calculate warped texture coordinates & gradient information
      float2 WarpTex = 0.0;
      WarpTex = MainTex - 0.5; // Pull into [-0.5, 0.5) range
      WarpTex -= Vectors; // Inverse warp in the [-0.5, 0.5) range
      WarpTex = saturate(WarpTex + 0.5); // Push and clamp into [0.0, 1.0) range
      float2 PixelSize = fwidth(MainTex);

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
      float IxIx = 0.0;
      float IyIy = 0.0;
      float IxIy = 0.0;
      float IxIt = 0.0;
      float IyIt = 0.0;
      float WSum = 0.0;

      // Get center textures (this is for the spatial weighting)
      float3 CenterT = Cache[Get1DIndexFrom2D(int2(2, 2), CacheWidth)];
      float3 CenterI = GetPlanesYUV(SampleI, WarpTex);

      [unroll]
      for (int i = 0; i < FetchGridSize; i++)
      {
         // Get cached data
         float3 North = Cache[Get1DIndexFrom2D(P[i].zw + int2(0, -1), CacheWidth)];
         float3 South = Cache[Get1DIndexFrom2D(P[i].zw + int2(0, 1), CacheWidth)];
         float3 East = Cache[Get1DIndexFrom2D(P[i].zw + int2(1, 0), CacheWidth)];
         float3 West = Cache[Get1DIndexFrom2D(P[i].zw + int2(-1, 0), CacheWidth)];
         float3 R0 = Cache[Get1DIndexFrom2D(P[i].zw, CacheWidth)];

         // Get R0 and R1 to calculate temporal gradient
         bool IsCenter = (P[i].x == 0) && (P[i].y == 0);
         int OffsetID = abs(P[i].x) + abs(P[i].y);
         float2 Offset = float2(P[i].xy);

         // Get dynamic data
         float2 R1Tex = WarpTex + (Offset * PixelSize);
         float3 R1 = IsCenter ? CenterI : GetPlanesYUV(SampleI, R1Tex);
         float3 It = 0.0;

         // Calculate bilateral weighting
         float Weight = 0.0;

         // Calculate range weights
         if (IsCenter)
         {
            Weight = 1.0;
         }
         else
         {
            It = R0 - CenterT;
            Weight += dot(It, It);
            It = R1 - CenterI;
            Weight += dot(It, It);
            Weight = 1.0 / (1.0 + Weight);
            Weight *= Weight;
         }

         // Accumulate weight
         WSum += (Weight * SWeights[OffsetID]);

         // Immediately calculate spatial gradients
         float3 Ix = (West * 0.5) - (East * 0.5);
         float3 Iy = (North * 0.5) - (South * 0.5);
         It = R1 - R0;

         // Summate the weighted contributions
         IxIx += (dot(Ix, Ix) * Weight);
         IxIt += (dot(Ix, It) * Weight);
         IyIy += (dot(Iy, Iy) * Weight);
         IyIt += (dot(Iy, It) * Weight);
         IxIy += (dot(Ix, Iy) * Weight);
      }

      // Check if WSum is not 0
      WSum = (WSum == 0.0) ? 0.0 : 1.0 / WSum;

      // Normalized weighted variables
      IxIx *= WSum;
      IyIy *= WSum;
      IxIy *= WSum;
      IxIt *= WSum;
      IyIt *= WSum;

      /*
         Calculate Lucas-Kanade matrix
         ---
         [ Ix^2/D -IxIy/D] = [-IxIt]
         [-IxIy/D  Iy^2/D]   [-IyIt]
      */

      float2x2 A = float2x2(IxIx, IxIy, IxIy, IyIy);
      float2 B = float2(IxIt, IyIt);

      // Calculate C factor
      float2 E = -B;
      float N = dot(E, E);
      float D = dot(E, mul(A, E));
      float C = N / D;

      // Calculate -C * B
      float2 Flow = (abs(D) > 0.0) ? -C * B : 0.0;

      // Normalize motion vectors
      Flow *= PixelSize;

      // Propagate normalized motion vectors in Norm Range
      Vectors += Flow;

      // Clamp motion vectors to restrict range to valid lengths
      Vectors = clamp(Vectors, -1.0, 1.0);

      // Encode motion vectors to FLT16 format
      return SNORMtoFLT16_FLT2(Vectors);
   }

References
----------

- Baker, S., & Matthews, I. (2004). Lucas-kanade 20 years on: A unifying framework. International journal of computer vision, 56, 221-255.
- Rojas, R. (2010). Lucas-kanade in a nutshell. Freie Universit at Berlinn, Dept. of Computer Science, Tech. Rep.
- Titkov, V. V., Panin, S. V., Lyubutin, P. S., Chemezov, V. O., & Eremin, A. V. (2017). Application of Lucas-Kanade algorithm with weight coefficient bilateral filtration for the digital image correlation method. IOP Conference Series: Materials Science and Engineering, 177, 012039. https://doi.org/10.1088/1757-899X/177/1/012039
- Wikipedia contributors. (2024, May 15). Lucas-Kanade method. In Wikipedia, The Free Encyclopedia. Retrieved 18:46, July 3, 2025, from https://en.wikipedia.org/w/index.php?title=Lucas%E2%80%93Kanade_method&oldid=1223913530
