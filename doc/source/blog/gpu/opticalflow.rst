
Lucas-Kanade Optical Flow on The GPU
====================================

An optical flow algorithm estimates the motion between frames. Optical flow is essential in object detection, object recognition, motion estimation, video compression, and video effects.

This post covers an HLSL implementation of the Lucas-Kanade optical flow algorithm.

The Problem
-----------

The Lucas-Kanade method is a **local** technique that estimates movement between two frames with the following assumptions:

#. The two images are *different*
#. The two images have *small movement*

These assumptions are known as the **brightness-constancy** assumption.

.. math:: I(x, y, t) - I(x + u, y + v, t + 1) = 0

To estimate the local image flow, one would use a least-squares method to solve a system of equations within the window.

The standard Lucas-Kanade solves these systems of equations within a 3x3 window, which evenly considers diagonal and perpendicular directions.

The Pyramid Approach
--------------------

The 3x3 Lucas-Kanade does not work for large areas. We need an approach that does the following:

- Does not break the **brightness-constancy** assumption.

  #. The two images are *different*
  #. The two images have *small movement*

- Fast computation
- Covers areas larger than 3x3

The pyramid Lucas-Kanade algorithm is a solution, which consists of the following steps.

#. Build the current frame's mipmap pyramid
#. Set the initial motion vector to ``<0.0, 0.0>``
#. Compute optical flow from the smallest to the largest pyramid level
#. Immediately cache the current frame for the next frame
#. Filter the optical flow

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

      [unroll] for (int y2 = 1; y2 >= -1; --y2)
      {
         [unroll] for (int x2 = 1; x2 >= -1; --x2)
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
