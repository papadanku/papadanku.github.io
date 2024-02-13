
Chromaticity in HLSL
====================

Images often represent color in 3 channels: ``(R, G, B)`` - red, green, and blue. You can represent ``(R, G, B)`` in any range. For this post, the range is a minimum of **0.0** and a maximum of **1.0**.

Calculating Chromaticities
--------------------------

Formula
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

.. code-block:: c
   :caption: Source Code

   float3 GetRGBChromaticity(float3 Color)
   {
      float SumRGB = dot(Color, 1.0);
      float3 Chromaticity = saturate(Color / SumRGB);
      // Output the chromaticity's white point if the divisor is 0.0
      Chromaticity = (SumRGB == 0.0) ? 1.0 / 3.0 : Chromaticity;
      return Chromaticity;
   }

.. note::

   - ``dot(c.xyz, 1.0)`` optimizes 2 ``ADD`` instructions to 1 ``DP3`` instruction.
   - Undefined behavior happens when you divide by ``0``.
   - ``(SumRGB == 0.0) ? 1.0 / 3.0 : Chromaticity`` outputs the chromaticity's white point if the divisor is ``0.0``.

   Calculating Chromaticity White Point
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
