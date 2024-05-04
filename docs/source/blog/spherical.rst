
Spherical Chromaticity in HLSL
==============================

This post introduces a color space that computes chromaticity with angles.

Precision Loss in RG Chromaticity
---------------------------------

Pecision is a major drawback to RG chromaticity. In RG chromaticity, all possible values map into a right-triangle, eliminating half of the precision in integer buffers.

We can encode data that fits in the entire ``RG8`` range by calculating the angles between the channels.

Source Code
-----------

.. code-block:: c

    /*
        This code is based on the algorithm described in the following paper:
        Author(s): Joost van de Weijer, T. Gevers
        Title: "Robust optical flow from photometric invariants"
        Year: 2004
        DOI: 10.1109/ICIP.2004.1421433
        Link: https://www.researchgate.net/publication/4138051_Robust_optical_flow_from_photometric_invariants
    */

    float2 GetSphericalRG(float3 Color)
    {
        const float HalfPi = 1.0 / acos(0.0);

        // Precalculate (x*x + y*y)^0.5 and (x*x + y*y + z*z)^0.5
        float L1 = length(Color.rg);
        float L2 = length(Color.rgb);

        float2 Angles = 0.0;
        Angles[0] = (L1 == 0.0) ? 1.0 / sqrt(2.0) : Color.g / L1;
        Angles[1] = (L2 == 0.0) ? 1.0 / sqrt(3.0) : L1 / L2;

        return saturate(asin(abs(Angles)) * HalfPi);
    }
