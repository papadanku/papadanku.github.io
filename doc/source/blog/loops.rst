
Turning a Nested 2D Loop into 1D
================================

In GPU programming, you might sample a 2D window with a nested. However, a nested loop might be more inefficient than 1 loop.

This post is an example of how to sample a 3x3 window of offsets in 1 loop.

Source Code
-----------

::

   // Get required data to calculate main window data
   const int WindowSize = 3;
   const int WindowHalf = trunc(WindowSize / 2);

   // Start from the negative so we can process a window in 1 loop
   [loop] for (int i = 0; i < (WindowSize * WindowSize); i++)
   {
      float2 XY = -WindowHalf + float2(i % WindowSize, trunc(i / WindowSize));
   }

.. note::

   == ============ == ================= ==
   i#              X                    Y
   == ============ == ================= ==
   0  -1 + (0 % 3) -1 -1 + trunc(0 / 3) -1
   1  -1 + (1 % 3) 0  -1 + trunc(1 / 3) -1
   2  -1 + (2 % 3) 1  -1 + trunc(2 / 3) -1
   3  -1 + (3 % 3) -1 -1 + trunc(3 / 3) 0
   4  -1 + (4 % 3) 0  -1 + trunc(4 / 3) 0
   5  -1 + (5 % 3) 1  -1 + trunc(5 / 3) 0
   6  -1 + (6 % 3) -1 -1 + trunc(6 / 3) 1
   7  -1 + (7 % 3) 0  -1 + trunc(7 / 3) 1
   8  -1 + (8 % 3) 1  -1 + trunc(8 / 3) 1
   == ============ == ================= ==
