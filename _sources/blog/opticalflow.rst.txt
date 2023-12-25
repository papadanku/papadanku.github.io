
Lucas-Kanade Optical Flow in HLSL
=================================

An optical flow algorithm estimates the motion between frames. Optical flow is essential in object detection, object recognition, motion estimation, video compression, and video effects.

This post covers an HLSL implementation of Lucas-Kanade optical flow.

Algorithm
---------

The pyramid LK algorithm consists of the following steps.

#. Build the current frame’s mipmap pyramid

   Encode the image into chromaticity with ``GetSphericalRG()``

#. Filter the current frame with a Gaussian blur
#. Set the initial motion vector to ``<0.0, 0.0>``
#. Compute optical flow from the smallest to largest pyramid level

   Propagate the optical flow at each level

#. Filter the optical flow with a Gaussian blur
#. Store the current frame for use in the next frame

.. note::

   The code contains **generic** functions, so you may need to change some parts of the code so it is compatible with your setup.

.. code-block:: c
   :caption: Source Code

   /*
      [Functions]
   */

   float2 GetSphericalRG(float3 Color)
   {
      const float IHalfPi = 1.0 / acos(0.0);
      const float2 White = acos(rsqrt(float2(2.0, 3.0)));

      float2 DotC = 0.0;
      DotC.x = dot(Color.xy, Color.xy);
      DotC.y = dot(Color.xyz, Color.xyz);
      float2 P = (DotC == 0.0) ? White : acos(abs(Color.xz * rsqrt(DotC)));
      return saturate(P * IHalfPi);
   }

   /*
      [Functions]
   */

   // [-1.0, 1.0] -> [Width, Height]
   float2 DecodeVectors(float2 Vectors, float2 ImageSize)
   {
      return Vectors / abs(ImageSize);
   }

   // [Width, Height] -> [-1.0, 1.0]
   float2 EncodeVectors(float2 Vectors, float2 ImageSize)
   {
      return clamp(Vectors * abs(ImageSize), -1.0, 1.0);
   }

   /*
      Lucas-Kanade optical flow with bilinear fetches
      ---
      Calculate Lucas-Kanade optical flow by solving (A^-1 * B)
      [A11 A12]^-1 [-B1] -> [ A11/D -A12/D] [-B1]
      [A21 A22]^-1 [-B2] -> [-A21/D  A22/D] [-B2]
      ---
      [ Ix^2/D -IxIy/D] [-IxIt]
      [-IxIy/D  Iy^2/D] [-IyIt]
   */

   float2 GetPixelPyLK
   (
      float2 MainTex,
      float2 Vectors,
      sampler2D SampleI0,
      sampler2D SampleI1
   )
   {
      // Initialize variables
      float4 WarpTex;
      float IxIx = 0.0;
      float IyIy = 0.0;
      float IxIy = 0.0;
      float IxIt = 0.0;
      float IyIt = 0.0;

      // Get required data to calculate main texel data
      const float Pi2 = acos(-1.0) * 2.0;
      float2 PixelSize = fwidth(MainTex);

      // Calculate main texel data (TexelSize, TexelLOD)
      WarpTex = float4(MainTex, MainTex + Vectors);

      // Un-normalize data for processing
      WarpTex *= (1.0 / abs(PixelSize.xyxy));
      Vectors = DecodeVectors(Vectors, PixelSize);

      [unroll] for(int i = 1; i < 4; ++i)
      {
         [unroll] for(int j = 0; j < 4 * i; ++j)
         {
               float Shift = (Pi2 / (4.0 * float(i))) * float(j);
               float2 AngleShift = 0.0;
               sincos(Shift, AngleShift.x, AngleShift.y);
               float4 Tex = WarpTex + (AngleShift.xyxy * float(i));

               // Get spatial gradient
               float4 NS = (Tex.xyxy + float4(0.0, -1.0, 0.0, 1.0)) * PixelSize.xyxy;
               float4 EW = (Tex.xyxy + float4(-1.0, 0.0, 1.0, 0.0)) * PixelSize.xyxy;
               float2 N = tex2D(SampleI0, NS.xy).rg;
               float2 S = tex2D(SampleI0, NS.zw).rg;
               float2 E = tex2D(SampleI0, EW.xy).rg;
               float2 W = tex2D(SampleI0, EW.zw).rg;
               float2 Ix = E - W;
               float2 Iy = N - S;

               // Get temporal gradient
               float4 TexIT = Tex.xyxy * PixelSize.xyxy;
               float2 I0 = tex2D(SampleI0, TexIT.xy).rg;
               float2 I1 = tex2D(SampleI1, TexIT.zw).rg;
               float2 IT = I0 - I1;

               // IxIx = A11; IyIy = A22; IxIy = A12/A22
               IxIx += dot(Ix, Ix);
               IyIy += dot(Iy, Iy);
               IxIy += dot(Ix, Iy);

               // IxIt = B1; IyIt = B2
               IxIt += dot(Ix, IT);
               IyIt += dot(Iy, IT);
         }
      }

      /*
         Calculate Lucas-Kanade matrix
         ---
         [ Ix^2/D -IxIy/D] [-IxIt]
         [-IxIy/D  Iy^2/D] [-IyIt]
      */

      // Calculate A^-1 and B
      float D = determinant(float2x2(IxIx, IxIy, IxIy, IyIy));
      float2x2 A = float2x2(IyIy, -IxIy, -IxIy, IxIx) / D;
      float2 B = float2(-IxIt, -IyIt);

      // Calculate A^T*B
      float2 Flow = (D == 0.0) ? 0.0 : mul(B, A);

      // Propagate and encode vectors
      return EncodeVectors(Vectors + Flow, PixelSize);
   }
