
Lucas-Kanade Optical Flow in HLSL
=================================

An optical flow algorithm estimates the motion between frames. Optical flow is essential in object detection, object recognition, motion estimation, video compression, and video effects.

This post covers an HLSL implementation of Lucas-Kanade optical flow.

Algorithm
---------

The pyramid LK algorithm consists of the following steps.

#. Build the current frame's mipmap pyramid

   Encode the image into chromaticity with ``GetSphericalRG()``

#. Filter the current frame with a Gaussian blur
#. Set the initial motion vector to ``<0.0, 0.0>``
#. Compute optical flow from the smallest to largest pyramid level

   Propagate the optical flow at each level

#. Filter the optical flow with a Gaussian blur
#. Store the current frame for use in the next frame

.. note::

   The code contains **generic** functions, so you may need to change some parts of the code so it is compatible with your setup.

Source Code
-----------

::

    /*
        This code is based on the algorithm described in the following paper:
        Author(s): Joost van de Weijer, T. Gevers
        Title: "Robust optical flow from photometric invariants"
        Year: 2004
        DOI: 10.1109/ICIP.2004.1421433
        Link: https://www.researchgate.net/publication/4138051_Robust_optical_flow_from_photometric_invariants
    */

    /*
        Lucas-Kanade optical flow with bilinear fetches.
        ---
        The algorithm is motified to not output in pixels, but normalized displacements
        ---
        Calculate Lucas-Kanade optical flow by solving (A^-1 * B)
        [A11 A12]^-1 [-B1] -> [ A11/D -A12/D] [-B1]
        [A21 A22]^-1 [-B2] -> [-A21/D  A22/D] [-B2]
        ---
        [ Ix^2/D -IxIy/D] [-IxIt]
        [-IxIy/D  Iy^2/D] [-IyIt]
    */

    float2 LucasKanade
    (
        float2 MainTex, // Texture coordinates
        float2 Vectors, // Previous motion vectors [-1.0, 1.0)
        sampler2D SampleI0, // Previous frame
        sampler2D SampleI1 // Current frame
    )
    {
        // Initialize variables
        float4 WarpTex;
        float IxIx = 0.0;
        float IyIy = 0.0;
        float IxIy = 0.0;
        float IxIt = 0.0;
        float IyIt = 0.0;

        // Initiate main & warped texture coordinates
        WarpTex = MainTex.xyxy;

        // Calculate warped texture coordinates
        WarpTex.zw -= 0.5; // Pull into [-0.5, 0.5) range
        WarpTex.zw += Vectors; // Warp in [-HalfMax, HalfMax) range
        WarpTex.zw = saturate(WarpTex.zw + 0.5); // Push and clamp into [0.0, 1.0) range

        // Get gradient information
        float4 TexIx = ddx(WarpTex);
        float4 TexIy = ddy(WarpTex);
        float2 PixelSize = abs(TexIx.xy) + abs(TexIy.xy);

        // Get required data to calculate main window data
        const int WindowSize = 3;
        const int WindowHalf = trunc(WindowSize / 2);

        [loop] for (int i = 0; i < (WindowSize * WindowSize); i++)
        {
            float2 Kernel = -WindowHalf + float2(i % WindowSize, trunc(i / WindowSize));

            // Get temporal gradient
            float4 TexIT = WarpTex.xyzw + (Kernel.xyxy * PixelSize.xyxy);
            float2 I0 = tex2Dgrad(SampleI0, TexIT.xy, TexIx.xy, TexIy.xy).rg;
            float2 I1 = tex2Dgrad(SampleI1, TexIT.zw, TexIx.zw, TexIy.zw).rg;
            float2 IT = I0 - I1;

            // Get spatial gradient
            float4 OffsetNS = Kernel.xyxy + float4(0.0, -1.0, 0.0, 1.0);
            float4 OffsetEW = Kernel.xyxy + float4(-1.0, 0.0, 1.0, 0.0);
            float4 NS = WarpTex.xyxy + (OffsetNS * PixelSize.xyxy);
            float4 EW = WarpTex.xyxy + (OffsetEW * PixelSize.xyxy);
            float2 N = tex2Dgrad(SampleI0, NS.xy, TexIx.xy, TexIy.xy).rg;
            float2 S = tex2Dgrad(SampleI0, NS.zw, TexIx.xy, TexIy.xy).rg;
            float2 E = tex2Dgrad(SampleI0, EW.xy, TexIx.xy, TexIy.xy).rg;
            float2 W = tex2Dgrad(SampleI0, EW.zw, TexIx.xy, TexIy.xy).rg;
            float2 Ix = E - W;
            float2 Iy = N - S;

            // IxIx = A11; IyIy = A22; IxIy = A12/A22
            IxIx += dot(Ix, Ix);
            IyIy += dot(Iy, Iy);
            IxIy += dot(Ix, Iy);

            // IxIt = B1; IyIt = B2
            IxIt += dot(Ix, IT);
            IyIt += dot(Iy, IT);
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
        float2 Flow = (D > 0.0) ? mul(B, A) : 0.0;

        // Normalize motion vectors
        Flow *= PixelSize;

        // Propagate normalized motion vectors in Norm Range
        Vectors += Flow;

        // Clamp motion vectors to restrict range to valid lengths
        Vectors = clamp(Vectors, -1.0, 1.0);

        return Vectors;
    }
