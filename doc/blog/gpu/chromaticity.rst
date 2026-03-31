
Image Chromaticity on the GPU
=============================

Images often represent color using three channels: :math:`(R, G, B)`. For this document, we assume the range of each channel is :math:`[0.0, 1.0)`.

Normalized RGB
--------------

Normalized RGB is a method of representing a color's chromaticity by scaling its components such that their sum equals 1. This removes the luminance information and is commonly used in color science.

Output Values
^^^^^^^^^^^^^

The output values represent the chromaticity of a color. They can be represented in two ways:

- :math:`(r, g, b)`: A 3D vector where the sum of the components equals 1.

  - :math:`(1, 0, 0)`: 100% red
  - :math:`(0, 1, 0)`: 100% green
  - :math:`(0, 0, 1)`: 100% blue

- :math:`(r, g)`: A 2D representation, often used in a chromaticity diagram. The blue component is implied since :math:`b = 1 - r - g`.

  - :math:`(1, 0)`: 100% red
  - :math:`(0, 1)`: 100% green
  - :math:`(0, 0)`: 100% blue (implied)

Normalized RG/RGB Formulas
^^^^^^^^^^^^^^^^^^^^^^^^^^

The normalized chromaticity coordinates (:math:`r`, :math:`g`, and :math:`b`) are calculated by dividing each color component (:math:`R`, :math:`G`, and :math:`B`) by the sum of all three. This ensures the sum of the new components is always equal to one.

.. math::

   r = \frac{R}{R+G+B}\\
   \\
   g = \frac{G}{R+G+B}\\
   \\
   b = \frac{B}{R+G+B}

.. note::

   The sum of the normalized components is always equal to one: :math:`r + g + b = 1`.

Normalized RG/RGB White-Point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A white-point in normalized chromaticity represents a perfect white light source where the red, green, and blue components are all equal.

.. math::

   R=G=B

When :math:`R`, :math:`G`, and :math:`B` are equal, the normalized formulas simplify to a specific point:

.. math::

   r = g = b = \frac{1}{3}

Source Code
^^^^^^^^^^^

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
