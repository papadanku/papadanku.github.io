
Image Chromaticity on the GPU
=============================

Images often represent color using three channels: (R, G, B) - red, green, and blue. For this document, we assume the range of each channel is [0.0, 1.0].

Normalized Chromaticity
-----------------------

Formulas
^^^^^^^^

Output (r, g, b)
   :(1.0, 0.0, 0.0): 100% red
   :(0.0, 1.0, 0.0): 100% green
   :(0.0, 0.0, 1.0): 100% blue

Output (r, g)
   :(1.0, 0.0): 100% red
   :(0.0, 1.0): 100% green
   :(0.0, 0.0): 100% blue (implied)

Normalized RG/RGB
"""""""""""""""""

.. math::

   r = \frac{R}{R+G+B}
   g = \frac{G}{R+G+B}
   b = \frac{B}{R+G+B}

   r+g+b = 1

Normalized RG/RGB White-Point
"""""""""""""""""""""""""""""

.. math::

   R = 1
   G = 1
   B = 1

   r = \frac{R}{R+G+B}
   g = \frac{G}{R+G+B}
   b = \frac{B}{R+G+B}

   r+g+b = 1

.. code-block:: hlsl

   float3 RGBtoChromaticityRGB(float3 Color)
   {
      // Optimizes 2 ADD instructions into 1 DP3 instruction.
      float SumRGB = dot(Color, 1.0);
      float3 Chromaticity = saturate(Color / SumRGB);

      // Output the chromaticity's white point if the divisor is 0.0.
      // Prevents undefined behavior when dividing by 0.
      Chromaticity = (SumRGB == 0.0) ? float3(1.0 / 3.0) : Chromaticity;

      return Chromaticity;
   }

Spherical Chromaticity
----------------------

This section introduces a color space that represents chromaticity using angles.

Precision Loss in RG Chromaticity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A significant drawback of RG chromaticity is precision loss. All possible values map to a right triangle, effectively halving the precision in integer buffers.

Spherical chromaticity encodes data that utilizes the entire RG8 range by calculating angles between the color channels.

.. code-block:: hlsl

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
