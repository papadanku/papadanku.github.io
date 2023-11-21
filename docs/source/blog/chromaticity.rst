
Chromaticity in HLSL
====================

Images often represent color in 3 channels: ``(R, G, B)`` - red, green, and blue. You can represent ``(R, G, B)`` in any range. For this post, the range is a minimum of **0.0** and a maximum of **1.0**.

“What is Chromaticity?”
-----------------------

You have **ColorA**, with an RGB of ``(0.0, 0.0, 0.1)``. **ColorA** is 100% blue. Chromaticity represents ``(R, G, B)`` as percentages proportional to the overall color.

“How Do I Compute 100% Blue?”
-----------------------------

You get **chromaticity** by computing ``(R,G,B)/(R+G+B)``. This table highlights steps to get **ColorA**\ ’s chromaticity.

======= =======================================
Step    Equation
======= =======================================
Formula ``(r,g,b) / sum(r,g,b)``
1       ``(0.0, 0.0, 0.1) / (0.0 + 0.0 + 0.1)``
2       ``(0.0, 0.0, 0.1) / (0.1)``
3       ``(0.0, 0.0, 1.0)``
======= =======================================

What Chromaticities Represent
-----------------------------

This table represents what certain chromaticities mean.

=================== ==========
RGB Chromaticity    Meaning
=================== ==========
``(1.0, 0.0, 0.0)`` 100% red
``(0.0, 1.0, 0.0)`` 100% green
``(0.0, 0.0, 1.0)`` 100% blue
=================== ==========

In RGB chromaticity, all channels sum to **1.0**. Therefore, you can represent RGB chromaticity in 2 channels. 2-channel chromaticity is **RG Chromaticity**.

=============== ==========
RG Chromaticity Meaning
=============== ==========
``(1.0, 0.0)``  100% red
``(0.0, 1.0)``  100% green
``(0.0, 0.0)``  100% blue
=============== ==========

.. code-block:: c
   :caption: Source Code

   float3 GetRGBChromaticity(float3 Color)
   {
      float SumRGB = dot(Color, 1.0);
      float3 Chromaticity = saturate(Color / SumRGB);
      Chromaticity = (SumRGB == 0.0) ? 1.0 / 3.0 : Chromaticity;
      return Chromaticity;
   }

.. note::

   - ``dot(c.xyz, 1.0)`` optimizes 2 ``ADD`` instructions to 1 ``DP3`` instruction.
   - Undefined behavior happens when you divide by 0.
   - ``(SumRGB == 0.0) ? 1.0 / 3.0 : Chromaticity`` outputs the chromaticity's white point if the divisor is 0.0.

   ======= =======================================
   Step    Equation
   ======= =======================================
   Formula ``(r,g,b) / sum(r,g,b)``
   1       ``(1.0, 1.0, 1.0) / (1.0 + 1.0 + 1.0)``
   2       ``(1.0, 1.0, 1.0) / (3.0)``
   3       ``(1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)``
   ======= =======================================
