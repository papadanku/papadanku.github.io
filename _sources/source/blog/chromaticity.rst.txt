
Chromaticity in HLSL
====================

Images often represent color in 3 channels: ``(R, G, B)`` - red, green, and blue. You can represent ``(R, G, B)`` in any range. For this post, the range is a minimum of **0.0** and a maximum of **1.0**.

Normalized Chromaticity
-----------------------

Formulas
^^^^^^^^

Normalized RG/RGB
   .. math::

      r = \frac{R}{R+G+B}\\
      g = \frac{G}{R+G+B}\\
      b = \frac{B}{R+G+B}\\
      \\
      r+g+b = 1

   Output :math:`(r,g,b)`
      :(1.0, 0.0, 0.0): 100% red
      :(0.0, 1.0, 0.0): 100% green
      :(0.0, 0.0, 1.0): 100% blue

   Output :math:`(r,g)`
      :\(1.0, 0.0\): 100% red
      :\(0.0, 1.0\): 100% green
      :\(0.0, 0.0\): 100% blue

Normalized RG/RGB White-Point
   .. math:: 

      R=1\\
      G=1\\
      B=1\\
      \\
      r = \frac{R}{R+G+B}\\
      g = \frac{G}{R+G+B}\\
      b = \frac{B}{R+G+B}\\
      \\
      r+g+b = 1

Source Code
^^^^^^^^^^^

::

   float3 GetRGBChromaticity(float3 Color)
   {
      // Optimizes 2 ADD instructions 1 DP3 instruction
      float SumRGB = dot(Color, 1.0);
      float3 Chromaticity = saturate(Color / SumRGB);
      // Output the chromaticity's white point if the divisor is 0.0
      // Prevents undefined behavior happens when you divide by 0
      Chromaticity = (SumRGB == 0.0) ? 1.0 / 3.0 : Chromaticity;
      return Chromaticity;
   }

Spherical Chromaticity
----------------------

This post introduces a color space that computes chromaticity with angles.

Precision Loss in RG Chromaticity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pecision is a major drawback to RG chromaticity. In RG chromaticity, all possible values map into a right-triangle, eliminating half of the precision in integer buffers.

We can encode data that fits in the entire ``RG8`` range by calculating the angles between the channels.

Source Code
^^^^^^^^^^^

::

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
