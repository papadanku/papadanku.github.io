
Lucas-Kanade Optical Flow on The GPU
====================================

An optical flow algorithm estimates the motion between frames. Optical flow is essential in object detection, object recognition, motion estimation, video compression, and video effects.

This post covers an HLSL implementation of Lucas-Kanade optical flow.

Algorithm
---------

The pyramid LK algorithm consists of the following steps.

#. Build the current frame's mipmap pyramid
#. Set the initial motion vector to ``<0.0, 0.0>``
#. Compute optical flow from the smallest to largest pyramid level
#. Immediately cache the current frame for the next frame
#. Filter the optical flow

Source Code
-----------

.. note::

   The code contains **generic** functions, so you may need to change some parts of the code so it is compatible with your setup.

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
        Lucas-Kanade optical flow with bilinear fetches. The algorithm is motified to not output in pixels, but normalized displacements.

        ---

        Gauss-Newton Steepest Descent Inverse Additive Algorithm

        https://www.ri.cmu.edu/pub_files/pub3/baker_simon_2002_3/baker_simon_2002_3.pdf

        ---

        Calculate Lucas-Kanade optical flow by solving (A^-1 * B)

        [A11 A12]^-1 [-B1] -> [ A11/D -A12/D] [-B1]
        [A21 A22]^-1 [-B2] -> [-A21/D  A22/D] [-B2]

        [ Ix^2/D -IxIy/D] [-IxIt]
        [-IxIy/D  Iy^2/D] [-IyIt]
    */

    float2 LucasKanade
    (
        float2 MainTex, // Texture coordinates
        float2 Vectors, // Previous motion vectors [-1.0, 1.0)
        sampler2D SampleT, // Template
        sampler2D SampleI // Image
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
        WarpTex.zw -= Vectors; // Inverse warp in the [-0.5, 0.5) range
        WarpTex.zw = saturate(WarpTex.zw + 0.5); // Push and clamp into [0.0, 1.0) range

        // Get gradient information
        float4 TexIx = ddx(WarpTex);
        float4 TexIy = ddy(WarpTex);
        float2 PixelSize = abs(TexIx.xy) + abs(TexIy.xy);

        // Get required data to calculate main window data
        const int WindowSize = 3;
        const int WindowHalf = WindowSize / 2;

        [loop] for (int i = 0; i < (WindowSize * WindowSize); i++)
        {
            float2 Kernel = float2(i % WindowSize, i / WindowSize) - WindowHalf;

            // Get temporal gradient
            float4 TexIT = WarpTex.xyzw + (Kernel.xyxy * PixelSize.xyxy);
            float3 T = tex2Dgrad(SampleT, TexIT.xy, TexIx.xy, TexIy.xy).xyz;
            float3 I = tex2Dgrad(SampleI, TexIT.zw, TexIx.zw, TexIy.zw).xyz;
            float3 IT = I - T;

            // Get spatial gradient
            float4 OffsetNS = Kernel.xyxy + float4(0.0, -1.0, 0.0, 1.0);
            float4 OffsetEW = Kernel.xyxy + float4(-1.0, 0.0, 1.0, 0.0);
            float4 NS = WarpTex.xyxy + (OffsetNS * PixelSize.xyxy);
            float4 EW = WarpTex.xyxy + (OffsetEW * PixelSize.xyxy);
            float3 N = tex2Dgrad(SampleT, NS.xy, TexIx.xy, TexIy.xy).xyz;
            float3 S = tex2Dgrad(SampleT, NS.zw, TexIx.xy, TexIy.xy).xyz;
            float3 E = tex2Dgrad(SampleT, EW.xy, TexIx.xy, TexIy.xy).xyz;
            float3 W = tex2Dgrad(SampleT, EW.zw, TexIx.xy, TexIy.xy).xyz;
            float3 Ix = E - W;
            float3 Iy = N - S;

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

            [ Ix^2/D -IxIy/D] [-IxIt]
            [-IxIy/D  Iy^2/D] [-IyIt]
        */

        /*
            Calculate Lucas-Kanade matrix
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

        // Normalize motion vectors
        Flow *= PixelSize;

        // Propagate normalized motion vectors in Norm Range
        Vectors += Flow;

        // Clamp motion vectors to restrict range to valid lengths
        Vectors = clamp(Vectors, -1.0, 1.0);

        return Vectors;
    }
