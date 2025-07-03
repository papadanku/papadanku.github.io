
Lucas-Kanade Optical Flow on The GPU
====================================

An optical flow algorithm estimates motion between consecutive video frames. Optical flow is essential in fields such as object detection, object recognition, motion estimation, video compression, and video effects.

This post covers an HLSL implementation of the Lucas-Kanade optical flow algorithm.

Optical Flow's Assumptions
--------------------------

When we use our eyes to track an object, we intuitively make certain assumptions to determine if an object has moved. For example, we can infer that a red dot has moved if we observe it maintaining its red color, but appearing in a different spatial location than it did a moment ago.

The Brightness Constancy Assumption \(BCA\)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Accurate motion estimation in video relies on fundamental simplifying assumptions.

#. The intensity \(brightness and color\) of an object's projection in two consecutive images remains *approximately constant*.
#. The movement of objects between two images is *small*.

These assumptions collectively form the basis of the **Brightness Constancy Assumption \(BCA\)**.

.. math::

   I(x, y, t) = I(x + u, y + v, t + 1)

.. note::

   **The Brightness Constancy Assumption has a limitation:** This assumption holds best for objects whose appearance does not significantly change between frames. For instance, it would struggle with a ball that constantly changes color or an object moving into shadow or direct light.

The Optical Flow Equation
^^^^^^^^^^^^^^^^^^^^^^^^^

Let's revisit the Brightness Constancy Assumption:

.. math:: I(x, y, t) = I(x + u, y + v, t + 1)

From this direct equality, it's not immediately obvious how to derive a formula for optical flow, as it simply states that the intensity at a point ``(x, y)`` in the previous image ``I`` at time ``t`` is equal to the intensity of the *same point* at a new position ``(x + u, y + v)`` in the current image at time ``t + 1``. Our goal is to find ``u`` and ``v``.

To achieve this, we need a mathematical way to approximate the instantaneous rate of change of image intensity from ``I(x, y, t)`` to ``I(x + u, y + v, t + 1)``. This is where derivatives and the Taylor series expansion become crucial.

We apply a first-order Taylor series expansion to the right-hand side of the Brightness Constancy Assumption, around the point ``(x, y, t)``:

.. math::

   I(x + u, y + v, t + 1) \approx I(x, y, t) + \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

Substituting this approximation back into the BCA and simplifying:

.. math::

   I(x, y, t) \approx I(x, y, t) + \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

   0 \approx \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v + \frac{\partial I}{\partial t}

This is the **Optical Flow Equation**. Rearranging it to isolate the temporal change:

.. math::

   \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v \approx -\frac{\partial I}{\partial t}

This is the spatial gradient \(how brightness changes horizontally and vertically\):

.. math:: \frac{\partial I}{\partial x}, \frac{\partial I}{\partial y}

This is the temporal gradient \(how brightness changes over time at a fixed location\):

.. math:: \frac{\partial I}{\partial t}

Our objective is to solve for ``u`` and ``v``, the horizontal and vertical components of the optical flow vector.

.. note::

   We use a first-order Taylor series expansion because the "small movement" assumption means that the changes regarding ``x``, ``y``, ``z`` are indeed small. This allows us to ignore higher-order terms in the expansion, which simplifies the math significantly while still providing a good approximation.

The Aperture Problem - In Practice
----------------------------------

Here's a practical demonstration of the Aperture Problem.

#. Obtain a string long enough that you cannot see its ends when viewing it through a small, fixed opening \(an "aperture"\).
#. Position the string behind the opening.
#. Angle the string at 45-degrees.
#. Now, slide the string through the opening in the following ways, ensuring its ends remain outside your view through the hole:

   - **Horizontally** slide the string across the opening.
   - **Vertically** slide the string across the opening.
   - **Diagonally** slide the string across the opening.

Do you perceive a difference in motion when sliding the string horizontally, vertically, or diagonally? Probably not, unless you can see parts of the string outside the constrained view of the opening.

**The Problem:** Your limited perception through the small aperture causes you to observe the string appearing to "move the same way" \(only perpendicular to its orientation\), regardless of its actual global movement direction. You cannot disambiguate its true 2D motion.

Let's examine the mathematical version of this problem.

The Aperture Problem - In Mathematics
-------------------------------------

Consider the Optical Flow Equation:

.. math::

   \frac{ \partial I }{ \partial x} u + \frac{\partial I}{\partial y} v \approx -\frac{\partial I}{\partial t}

Imagine you're back in your underfunded school's math class, and your teacher asks the class to solve the following single linear equation for both ``u`` and ``v``:

.. math:: 3u + 4v = 0

Possible solutions the class might propose include:

.. math::

   u = -4, \quad v = 3
   \\
   u = 4, \quad v = -3
   \\
   u = 0, \quad v = 0

This demonstrates that for a single pixel \(which acts as a tiny aperture\), the optical flow equation provides only one constraint on two unknowns \(``u`` and ``v``\). Consequently, there are infinitely many pairs of ``(u, v)`` that satisfy the equation. If you plot these solutions on a graph, they all lie on a single line, meaning the true direction of motion is ambiguous - only the component of motion perpendicular to the image gradient can be determined.

The Lucas-Kanade Approach to The Aperture Problem
-------------------------------------------------

The Lucas-Kanade method is a **local** technique designed to overcome the aperture problem by solving a system of optical flow equations within a small spatial window or neighborhood.

To estimate the local image flow for a given point, Lucas-Kanade employs a least-squares method. This method solves an overdetermined system of linear equations, where each pixel within the chosen window contributes an optical flow equation.

The standard Lucas-Kanade algorithm typically solves these systems of equations within a 3x3 window, as this size often provides a good balance, effectively considering motion components in various directions.

The Pyramid Approach
--------------------

The basic Lucas-Kanade method, while effective for small displacements, becomes less accurate for large motions. This is because large movements violate the "small movement" assumption inherent in the first-order Taylor expansion and the brightness constancy assumption. To handle larger motions while maintaining efficiency and adherence to assumptions, a hierarchical, or "pyramid," approach is used:

This approach ensures:

* It does not fundamentally break the **brightness constancy** assumption, as motion is estimated incrementally at different scales.
* It handles cases where the actual movement between two images is significant.
* It facilitates fast computation by starting with coarse motion estimates at lower resolutions.
* It effectively covers motion in areas larger than a 3x3 window by propagating estimates across pyramid levels.

The pyramid Lucas-Kanade algorithm consists of the following general steps:

#. Construct an image pyramid for the current frame and previous frame.
#. Initialize the motion vector \(flow\) at the coarsest pyramid level \(smallest image\) to ``0.0`` or a previous estimate.
#. Compute optical flow iteratively from the smallest \(coarsest\) pyramid level to the largest \(finest\) level. At each level, the flow from the coarser level is used to "warp" the image, reducing the remaining displacement, and then a refinement is calculated.
#. Cache the current frame \(or its pyramid\) for use as the "previous frame" in the next optical flow calculation.
#. Optionally, filter the computed optical flow vectors to remove noise or outliers.

Source Code
-----------

.. note::

   The code contains **generic** functions, so you may need to change some parts of the code so it is compatible with your setup.

.. code-block:: none
   :caption: Converting from 2D Grid Position to 1D Index

   /*
      Function to convert 2D row and column (0-indexed) to a 1D index.
      ZeroIndexGridPos.x: The 0-indexed row number.
      ZeroIndexGridPos.y: The 0-indexed column number.
      GridWidth: The total width of the grid (number of columns).
      Returns a 1D index.
   */
   int Get1DIndexFrom2D(int2 ZeroIndexGridPos, int GridWidth)
   {
      return (ZeroIndexGridPos.x * GridWidth) + ZeroIndexGridPos.y;
   }


.. code-block:: none
   :caption: Converting to Spherical RGB

   /*
      This code is based on the algorithm described in the following paper:
      Author(s): Joost van de Weijer, T. Gevers
      Title: "Robust optical flow from photometric invariants"
      Year: 2004
      DOI: 10.1109/ICIP.2004.1421433

      https://www.researchgate.net/publication/4138051_Robust_optical_flow_from_photometric_invariants
   */

   float3 RGBtoSphericalRGB(float3 RGB)
   {
      const float InvPi = 1.0 / acos(-1.0);

      // Precalculate (x*x + y*y)^0.5 and (x*x + y*y + z*z)^0.5
      float L1 = length(RGB.xyz);
      float L2 = length(RGB.xy);

      // .x = radius; .y = inclination; .z = azimuth
      float3 RIA;
      RIA.x = L1 / sqrt(3.0);
      RIA.y = (L1 == 0.0) ? 1.0 / sqrt(3.0) : saturate(RGB.z / L1);
      RIA.z = (L2 == 0.0) ? 1.0 / sqrt(2.0) : saturate(RGB.x / L2);

      // Scale the angles to [-1.0, 1.0) range
      RIA.yz = (RIA.yz * 2.0) - 1.0;

      // Calculate inclination and azimuth and normalize to [0.0, 1.0)
      RIA.yz = acos(RIA.yz) * InvPi;

      return RIA;
   }

.. code-block:: none
   :caption: Lucas-Kanade Optical Flow

   /*
      Lucas-Kanade optical flow with bilinear fetches.

      ---

      Gauss-Newton Steepest Descent Inverse Additive Algorithm

      Baker, S., & Matthews, I. (2004). Lucas-kanade 20 years on: A unifying framework. International journal of computer vision, 56, 221-255.

      https://www.researchgate.net/publication/248602429_Lucas-Kanade_20_Years_On_A_Unifying_Framework_Part_1_The_Quantity_Approximated_the_Warp_Update_Rule_and_the_Gradient_Descent_Approximation
   */

   float2 LucasKanade(
      float2 MainPos,
      float2 MainTex,
      float2 Vectors,
      sampler2D SampleT,
      sampler2D SampleI
   )
   {
      // Initialize variables
      float IxIx = 0.0;
      float IyIy = 0.0;
      float IxIy = 0.0;
      float IxIt = 0.0;
      float IyIt = 0.0;

      // Calculate warped texture coordinates
      float2 WarpTex = MainTex;
      WarpTex -= 0.5; // Pull into [-0.5, 0.5) range
      WarpTex -= Vectors; // Inverse warp in the [-0.5, 0.5) range
      WarpTex = saturate(WarpTex + 0.5); // Push and clamp into [0.0, 1.0) range

      // Get gradient information
      float2 PixelSize = fwidth(MainTex);

      /*
         Template indecies:

            * = Indecies for calculating the temporal gradient (IT)
            - = Unused indecies

            00- 01  02  03  04-
            05  06* 07* 08* 09
            10  11* 12* 13* 14
            15  16* 17* 18* 19
            20- 21  22  23  24-

         Template (Row, Column):

            (0, 0) (0, 1) (0, 2) (0, 3) (0, 4)
            (1, 0) (1, 1) (1, 2) (1, 3) (1, 4)
            (2, 0) (2, 1) (2, 2) (2, 3) (2, 4)
            (3, 0) (3, 1) (3, 2) (3, 3) (3, 4)
            (4, 0) (4, 1) (4, 2) (4, 3) (4, 4)
      */

      // Initiate TemplateCache
      const int TemplateGridSize = 5;
      const int TemplateCacheSize = TemplateGridSize * TemplateGridSize;
      float3 TemplateCache[TemplateCacheSize];

      // Create TemplateCache
      int TemplateCacheIndex = 0;
      [unroll] for (int y1 = 2; y1 >= -2; y1--)
      {
         [unroll] for (int x1 = 2; x1 >= -2; x1--)
         {
            bool OutOfBounds = (abs(x1) == 2) && (abs(y1) == 2);
            float2 Tex = MainTex + (float2(x1, y1) * PixelSize);
            TemplateCache[TemplateCacheIndex] = OutOfBounds ? 0.0 : tex2D(SampleT, Tex).xyz;
            TemplateCacheIndex += 1;
         }
      }

      // Loop over the starred template areas
      int TemplateGridPosIndex = 0;
      int2 TemplateGridPos[9] =
      {
         int2(1, 1), int2(1, 2), int2(1, 3),
         int2(2, 1), int2(2, 2), int2(2, 3),
         int2(3, 1), int2(3, 2), int2(3, 3),
      };

      [unroll] for (int y2 = 1; y2 >= -1; y2--)
      {
         [unroll] for (int x2 = 1; x2 >= -1; x2--)
         {
            int2 GridPos = TemplateGridPos[TemplateGridPosIndex];

            // Calculate temporal gradient
            float3 I = tex2D(SampleI, WarpTex + (float2(x2, y2) * PixelSize)).xyz;
            float3 T = TemplateCache[Get1DIndexFrom2D(GridPos, TemplateGridSize)];
            float3 It = I - T;

            // Calculate spatial gradients with central difference operator
            float3 N = TemplateCache[Get1DIndexFrom2D(GridPos + int2(1, 0), TemplateGridSize)];
            float3 S = TemplateCache[Get1DIndexFrom2D(GridPos + int2(-1, 0), TemplateGridSize)];
            float3 E = TemplateCache[Get1DIndexFrom2D(GridPos + int2(0, -1), TemplateGridSize)];
            float3 W = TemplateCache[Get1DIndexFrom2D(GridPos + int2(0, 1), TemplateGridSize)];
            float3 Ix = (W - E) / 2.0;
            float3 Iy = (N - S) / 2.0;

            // IxIx = A11; IyIy = A22; IxIy = A12/A22
            IxIx += dot(Ix, Ix);
            IyIy += dot(Iy, Iy);
            IxIy += dot(Ix, Iy);

            // IxIt = B1; IyIt = B2
            IxIt += dot(Ix, It);
            IyIt += dot(Iy, It);

            // Increment TemplatePos
            TemplateGridPosIndex += 1;
         }
      }

      /*
         Calculate Lucas-Kanade matrix
         ---
         [ Ix^2/D -IxIy/D] [-IxIt]
         [-IxIy/D  Iy^2/D] [-IyIt]
      */

      // Construct matrices
      float2x2 A = float2x2(IxIx, IxIy, IxIy, IyIy);
      float2 B = float2(IxIt, IyIt);

      // Calculate C factor
      float N = dot(B, B);
      float2 DotBA = float2(dot(B, A[0]), dot(B, A[1]));
      float D = dot(DotBA, B);
      float C = N / D;

      // Calculate -C*B
      float2 Flow = (abs(D) > 0.0) ? -mul(C, B) : 0.0;

      // Propagate motion vectors
      Vectors += Flow;

      return Vectors;
   }
