
Converting a Nested 2D Loop to 1D
=================================

On GPUs, a single 1D loop can be more efficient than a nested 2D loop for tasks like sampling a 2D window. Here's how to sample a 3x3 window of offsets using a 1D loop.

.. code-block:: none
   :caption: Source Code

   // Window size.
   const int WindowSize = 3;
   const int WindowHalf = WindowSize / 2; // Integer division.

   // 1D loop to iterate over 3x3 window.
   for (int i = 0; i < (WindowSize * WindowSize); i++)
   {
      float2 XY = float2(i % WindowSize, i / WindowSize) - WindowHalf;
   }

Example: 3x3 Window Offsets
---------------------------

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
