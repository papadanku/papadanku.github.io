
Multilevel Adaptive Side-Window Bilateral Upsampling on the GPU
===============================================================

This document proposes an adaptive, multilevel, side-window bilateral upsampling filter designed for motion vectors.

.. seealso::

   Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

   Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

   Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 8758-8766.

Bilateral Upsampling
--------------------

Bilateral upsampling uses a high-resolution guide image to interpolate a low-resolution target image. Unlike standard linear interpolation, which assumes a smoothness prior, this technique uses the guide image to identify structural edges.

The filter computes a weighted average of nearby low-resolution pixels. The weight for each pixel depends on two factors:

* **Spatial Distance**: Pixels closer to the target location contribute more.
* **Intensity Difference**: Pixels in the guide image with similar intensities to the target guide pixel contribute more.

This dual-weighting ensures that only pixels on the same side of an edge contribute to the result, effectively preserving structural boundaries.

Adaptive Weights
----------------

Adaptive bilateral upsampling improves the process by dynamically adjusting the filter's sensitivity based on local image characteristics. Instead of using global constants for the range variance, the algorithm calculates variances within the filtering window at two different scales: the global window and individual side windows.

In homogeneous regions (low variance), the filter allows a wider range of pixels to contribute, enhancing smoothing. In edge regions (high variance), the filter becomes more restrictive. This adaptive behavior minimizes artifacts and ensures that the filter's strength is proportional to the local content's complexity.

Global Window: Gradient-based Coherence
---------------------------------------

To determine the overall range sensitivity, the filter calculates a normalized squared coherence based on the local image gradients, :math:`\mathbf{G}_x` and :math:`\mathbf{G}_y`. This coherence value, which ranges from 0 to 1, quantifies the directional consistency of the gradients within the window. A high coherence indicates a strong, well-defined edge, whereas a low coherence suggests a more isotropic or homogeneous region.

The coherence :math:`C` is defined as:

.. math::

   C = \frac{4 \cdot \left[ \left( \frac{\|\mathbf{G}_x\|^2 - \|\mathbf{G}_y\|^2}{2} \right)^2 + (\mathbf{G}_x \cdot \mathbf{G}_y)^2 \right]}{(\|\mathbf{G}_x\|^2 + \|\mathbf{G}_y\|^2)^2}

The coherence :math:`C` is used as the squared Full Width at Half Maximum (:math:`\text{FWHM}^2`) parameter for a Lorentzian distribution, which determines the range weights :math:`w_r`. This ensures that the filter's sensitivity to intensity differences is scaled by the local gradient coherence:

.. math::

   w_r = \frac{A \cdot (C/4)}{(C/4) + \|d\|^2}

Side Windows: Coefficient of Variation Weighting
------------------------------------------------

For the "soft-selection" of side windows, the filter calculates Van Valen's Multivariate Coefficient of Variation (CoV) for each window. This allows the algorithm to weight windows based on their local stability. The CoV is computed using the trace of the covariance matrix :math:`\text{Tr}(\Sigma)` and the squared norm of the mean :math:`\|\bar{x}\|^2`:

.. math::

   \text{CoV}^2 = \frac{\text{Tr}(\Sigma)}{\|\bar{x}\|^2}

An exponential decay based on the absolute Coefficient of Variation (CoV) is used to weight the contribution of each side window, providing a smooth transition based on local stability:

.. math::

   w_v = \text{Lorentzian}(\text{CoV}; \text{FWHM}=\text{GVariance})

Using the Side Window Filter
----------------------------

Conventional filtering algorithms center the local window on the target pixel. When a pixel lies near an edge, this centered window captures samples from both sides of the boundary. Averaging these dissimilar pixels blurs the edge.

The algorithm evaluates multiple side windows, covering cardinal directions and corners. Instead of selecting a single optimal window, it combines their results using a variance-weighted average. This "soft-selection" approach allows the filter to prioritize windows that align with local edges while still incorporating information from neighboring regions.

The SWF framework supports various filter implementations:

* **Box Filter**: Computes the arithmetic mean of all pixels within the side window.
* **Gaussian Filter**: Applies a weighted average where pixels closer to the target pixel contribute more.
* **Median Filter**: Selects the median value from the window, which effectively removes noise while maintaining edge sharpness.
* **Bilateral Filter**: Weights pixels based on both spatial distance and intensity difference, ensuring only pixels with similar values contribute to the result.

The implemented version follows these steps:

#. **Shared Data Gathering**: A two-pass process that first collects the neighborhood samples and then computes the range weights using the local coherence-based variance.
#. **Kernel Generation**: Define a set of kernels representing eight side windows: four cardinal directions and four corners.
#. **Side Window Statistics Calculation**: For each window, compute the local mean :math:`\mu_W` and variance :math:`\sigma^2_W`.
#. **Bilateral Weighted Estimation**: For each window, calculate a bilateral-weighted mean :math:`\mu_{W, \text{bilat}}`. The range weight is adaptively adjusted using the global coherence-based variance:

   .. math::

      w_r = \text{Lorentzian}(\|d\|^2; \text{FWHM}^2 = C)

#. **Variance-Weighted Combination**: Combine the estimated means using their stability weights (derived from the Coefficient of Variation) as weights:

   .. math::

      \mu_{\text{final}} = \frac{\sum \mu_{W_i, \text{bilat}} \cdot w_{v,i}}{\sum w_{v,i}}

Karis Averaging for Motion Vectors
----------------------------------

In temporal upsampling, "pulsation" occurs when a filter's selection jumps abruptly between different windows across frames. A standard minimum-variance selection can be highly sensitive to noise, causing these sudden temporal discontinuities.

To mitigate this, we implement a technique inspired by Karis averaging. While standard Karis averaging uses pixel brightness to prevent over-brightening, this implementation uses the sum of pixel variances to infer local stability. This ensures that the contribution of each side window is proportional to its stability, resulting in smoother and more coherent upsampled motion vectors.

Using Image Pyramids
--------------------

A multilevel scheme employs an image pyramid for recursive upsampling. Instead of a single-step upsampling operation, the algorithm increases resolution incrementally (e.g., in :math:`2 \times 2` stages).

At each pyramid level, the adaptive side-window bilateral filter is applied to the current resolution. This recursive refinement minimizes aliasing artifacts and reduces the overall computational cost compared to a single-step high-resolution filter.

Multilevel Adaptive Side-Window Bilateral Upsampling
----------------------------------------------------

The proposed technique integrates the following components:

* **Adaptive Weighting**: Dynamically adjusts the filter's range parameters based on local image variance.
* **Side Window Filtering**: Evaluates multiple shifted windows to identify the one that best aligns with the target pixel.
* **Image Pyramids**: Employs recursive upsampling to optimize computational efficiency.

.. code-block:: hlsl
   :caption: Helper Math Functions

   float GetLorentzian1D(float X, float A, float FWHM)
   {
      float HWHM = FWHM / 2.0;
      float HWHM_Sq = HWHM * HWHM;
      float X_Sq = X * X;
      return (A * HWHM_Sq) / (HWHM_Sq + X_Sq);
   }

   float GetLorentzian1D_Fast(float X_Sq, float A, float FWHM_Sq)
   {
      // (FWHM / 2)^2 = FWHM^2 / 4
      float HWHM_Sq = FWHM_Sq / 4.0;
      return (A * HWHM_Sq) / (HWHM_Sq + X_Sq);
   }

.. code-block:: hlsl
   :caption: Variance-Weighted Adaptive, Multilevel, Side-Window Bilateral Upsampling

   /*
      This is an optimized, self-guided version for Joint Bilateral Upsampling implemented in HLSL.

      Inspired by Kopf et al. (2007) and Riemens et al. (2009).

      ---

      Kopf, J., Cohen, M. F., Lischinski, D., & Uyttendaele, M. (2007). Joint bilateral upsampling. ACM SIGGRAPH 2007 Papers, 96. https://doi.org/10.1145/1275808.1276497

      Riemens, A. K., Gangwal, O. P., Barenbrug, B., & Berretty, R.-P. M. (2009). Multistep joint bilateral depth upsampling. In M. Rabbani & R. L. Stevenson (Eds.), SPIE Proceedings (Vol. 7257, p. 72570M). SPIE. https://doi.org/10.1117/12.805640

      Yin, H., Gong, Y., & Qiu, G. (2019). Side window filtering. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition (pp. 8758-8766).
   */

   struct SharedData_SideWindow_Bilateral
   {
      // Shared constants
      int ArrayImageLength;
      int SideWindowSize_Corner;
      int SideWindowSize_Cardinal;

      // Shared between side windows
      float2 ArrayImages[9];
      float ArrayDistances[9];
      float2 SideWindowMeans[8];
      float GVariance_Sq;

      // Shared for final calculation
      float2 Reference;
   };

   struct SideWindow_Bilateral
   {
      float Masks[9];
      float Size;

      float2 Sum;
      float SumWeight;

      float Influence;
   };

   void GetSharedData_SideWindow_Bilateral(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex,
      out SharedData_SideWindow_Bilateral Output
   )
   {
      const int ArrayImageLength = 9;
      const int SideWindowSize_Corner = 4;
      const int SideWindowSize_Cardinal = 6;

      // Precompute constants (side windows)
      Output.SideWindowSize_Corner = SideWindowSize_Corner;
      Output.SideWindowSize_Cardinal = SideWindowSize_Cardinal;

      // Initialize variables
      Output.ArrayImageLength = ArrayImageLength;
      Output.Reference = tex2D(Guide, Tex).xy;

      // Precompute (static)
      float2 PixelSize = fwidth(Tex.xy);

      /*
         Gather samples:

         0 3 6 [ North West | North  | North East ]
         1 4 7 [    West    | Center |    East    ]
         2 5 8 [ South West | South  | South East ]
      */

      // Initialize counter here
      int ImageIndex0 = 0;

      [unroll]
      for (int x0 = -1; x0 <= 1; x0++)
      {
         [unroll]
         for (int y0 = -1; y0 <= 1; y0++)
         {
            // *2 because the lower sample takes a 2 texel footprint.
            float2 Delta = float2(x0, y0) * 2.0;
            float2 Offset = Tex + (Delta * PixelSize);
            Output.ArrayImages[ImageIndex0] = tex2D(Image, Offset).xy;

            ImageIndex0 += 1;
         }
      }

      /*
         Compute the Coherance.

         Simplication of the factor inside the square root (S):

            1. Tr(M)^2 - 4det(M)
            2. (a + c)^2 - 4(ac - b^2)
            3. a^2 + 2ac + c^2 - 4ac + 4b^2
            4. a^2 - 2ac + c^2 + 4b^2
            5. (a - c)^2 + 4b^2

            1. E = (Tr(M) +- sqrt((a - c)^2 + 4b^2)) / 2
            2. E = (Tr(M) / 2) +- sqrt(((a - c)^2 / 4) + (4b^2 / 4))
            3. E = (Tr(M) / 2) +- sqrt(((a - c) / 2)^2 + b^2)

            E1 = (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2)
            E2 = (Tr(M) / 2) - sqrt(((a - c) / 2)^2 + b^2)

         Now we need to compute C: (E1 - E2) / (E1 + E2)

            E1 - E2:

               1. ((Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2)) - ((Tr(M) / 2) - sqrt(((a - c) / 2)^2 + b^2))
               2. (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2) - (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2)
               3. sqrt(((a - c) / 2)^2 + b^2) + sqrt(((a - c) / 2)^2 + b^2)
               4. 2 * sqrt(((a - c) / 2)^2 + b^2)

            E1 + E2:

               1. (Tr(M) / 2) + sqrt(((a - c) / 2)^2 + b^2) + ((Tr(M) / 2) - sqrt(((a - c) / 2)^2 + b^2))
               2. (Tr(M) / 2) + (Tr(M) / 2)
               3. 2 * (Tr(M) / 2)
               4. Tr(M)

            Therefore: (2 * sqrt(((a - c) / 2)^2 + b^2)) / Tr(M)
      */

      const float K_H[ArrayImageLength] =
      {
         -1.0 / 4.0, -2.0 / 4.0, -1.0 / 4.0,
          0.0,        0.0,        0.0,
          1.0 / 4.0,  2.0 / 4.0,  1.0 / 4.0
      };

      const float K_V[ArrayImageLength] =
      {
         -1.0 / 4.0, 0.0, 1.0 / 4.0,
         -2.0 / 4.0, 0.0, 2.0 / 4.0,
         -1.0 / 4.0, 0.0, 1.0 / 4.0
      };

      float2 Gx = 0.0;
      float2 Gy = 0.0;

      // Completely unrolled to avoid SM3 loop register index penalties
      [unroll]
      for (int i = 0; i < ArrayImageLength; i++)
      {
         Gx += (Output.ArrayImages[i] * K_H[i]);
         Gy += (Output.ArrayImages[i] * K_V[i]);
      }

      float DotGxGx = dot(Gx, Gx);
      float DotGyGy = dot(Gy, Gy);
      float DotGxGy = dot(Gx, Gy);

      float Trace = (DotGxGx + DotGyGy);          // Element (a + c)
      float Diff  = (DotGxGx - DotGyGy) * 0.5;    // Element (a - c) / 2
      float N = (Diff * Diff) + (DotGxGy * DotGxGy);
      float D = Trace * Trace;

      // Normalized Squared Coherence: 0 (flat), (highly directional edge)
      float Coherence = (D > 0.0) ? (4.0 * N) / D : 0.0;

      // Map into your global variance framework
      Output.GVariance_Sq = Coherence + 1e-7;

      // Reset counter and start again
      int ImageIndex1 = 0;

      [unroll]
      for (int x1 = -1; x1 <= 1; x1++)
      {
         [unroll]
         for (int y1 = -1; y1 <= 1; y1++)
         {
            // Compute shared Weight (Range) here.
            float2 Delta = Output.ArrayImages[ImageIndex1] - Output.Reference;
            float DistRange_Sq = dot(Delta, Delta);
            Output.ArrayDistances[ImageIndex1] = GetLorentzian1D_Fast(DistRange_Sq, 1.0, Output.GVariance);

            ImageIndex1 += 1;
         }
      }

      /*
         Construct array of kernels:

         [0] [3] [6]  (Top Row)
         [1] [4] [7]  (Middle Row)
         [2] [5] [8]  (Bottom Row)

         NORTH   SOUTH   EAST    WEST
         x x x   - - -   - x x   x x -
         x x x   x x x   - x x   x x -
         - - -   x x x   - x x   x x -

         NORTHWEST   NORTHEAST   SOUTHWEST   SOUTHEAST
         x x -       - x x       - - -       - - -
         x x -       - x x       x x -       - x x
         - - -       - - -       x x -       - x x
      */

      const float SideWindowWeight_Corner = 1.0 / float(Output.SideWindowSize_Corner);
      const float SideWindowWeight_Cardinal = 1.0 / float(Output.SideWindowSize_Cardinal);

      float2 Submeans[8];
      Submeans[0] = Output.ArrayImages[0].xy + Output.ArrayImages[1].xy; // Vertical Top-Left (V_TL)
      Submeans[1] = Output.ArrayImages[3].xy + Output.ArrayImages[4].xy; // Vertical Top-Mid (V_TM)
      Submeans[2] = Output.ArrayImages[6].xy + Output.ArrayImages[7].xy; // Vertical Top-Right (V_TR)
      Submeans[3] = Output.ArrayImages[1].xy + Output.ArrayImages[2].xy; // Vertical Bottom-Left (V_BL)
      Submeans[4] = Output.ArrayImages[4].xy + Output.ArrayImages[5].xy; // Vertical Bottom-Mid (V_BM)
      Submeans[5] = Output.ArrayImages[7].xy + Output.ArrayImages[8].xy; // Vertical Bottom-Right (V_BR)
      Submeans[6] = Output.ArrayImages[2].xy + Output.ArrayImages[5].xy; // Horizontal Bottom-Left (H_BL)
      Submeans[7] = Output.ArrayImages[5].xy + Output.ArrayImages[8].xy; // Horizontal Bottom-Right (H_BR)

      Output.SideWindowMeans[0] = Submeans[0] + Submeans[1]; // NW: [0 + 1] + [3 + 4]
      Output.SideWindowMeans[1] = Submeans[1] + Submeans[2]; // NE: [3 + 4] + [6 + 7]
      Output.SideWindowMeans[2] = Submeans[3] + Submeans[4]; // SW: [1 + 2] + [4 + 5]
      Output.SideWindowMeans[3] = Submeans[4] + Submeans[5]; // SE: [4 + 5] + [7 + 8]
      Output.SideWindowMeans[4] = Output.SideWindowMeans[0] + Submeans[2]; // N: [0 + 1 + 3 + 4] + [6 + 7]
      Output.SideWindowMeans[5] = Output.SideWindowMeans[2] + Submeans[5]; // S: [1 + 2 + 4 + 5] + [7 + 8]
      Output.SideWindowMeans[6] = Output.SideWindowMeans[0] + Submeans[6]; // W: [0 + 1 + 3 + 4] + [2 + 5]
      Output.SideWindowMeans[7] = Output.SideWindowMeans[1] + Submeans[7]; // E: [3 + 4 + 6 + 7] + [5 + 8]

      Output.SideWindowMeans[0] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[1] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[2] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[3] *= SideWindowWeight_Corner;
      Output.SideWindowMeans[4] *= SideWindowWeight_Cardinal;
      Output.SideWindowMeans[5] *= SideWindowWeight_Cardinal;
      Output.SideWindowMeans[6] *= SideWindowWeight_Cardinal;
      Output.SideWindowMeans[7] *= SideWindowWeight_Cardinal;
   }

   void GetSideWindow_Bilateral(
      in SharedData_SideWindow_Bilateral Input,
      in float2 Mean,
      inout SideWindow_Bilateral Block
   )
   {
      // Pre-compute Spatial distances.
      // .x = Center (0 + 0); .y = Diagonal (1 + 1); .z = Cardinal (0 + 1)
      const float Epsilon = 1e-7;
      const float3 SpatialDistances = exp2(-float3(0.0, 1.0, 2.0));

      // Initialize output members.
      Block.Sum = 0.0;
      Block.SumWeight = 0.0;

      // Initialize Outputs.
      int ImageIndex = 0;

      [unroll]
      for (int y = -1; y <= 1; y++)
      {
         [unroll]
         for (int x = -1; x <= 1; x++)
         {
            if (Block.Masks[ImageIndex] == 1)
            {
               // Compute Weight (Spatial).
               int SpatialOffset = abs(x) + abs(y);
               float WeightSpatial = SpatialDistances[SpatialOffset];

               // Fetch Weight (Range) and combine.
               float WeightRange = Input.ArrayDistances[ImageIndex];
               float Weight = WeightSpatial * WeightRange;

               // Accumulate.
               Block.Sum += (Input.ArrayImages[ImageIndex] * Weight);
               Block.SumWeight += Weight;
            }

            ImageIndex += 1;
         }
      }

      /*
         Compute the SideWindow's Sample Coefficient of Variance (CoV).

         We use Van Valen's Multivariate Coefficient of Variation because of the computational simplicity.

         Tr = The Trace
         M = The Mean
      */

      // Constant: Sample Variance (Sigma)
      const float SigmaN = 1.0 / (float(Block.Size) - 1.0);

      /*
         We will compute the trace of the covariance matrix with vector MADs.

         | xx xy | <- We skip the xy/yx calculation of the matrix.
         | yx yy |
      */

      float2 SigmaVec = 0.0;

      [unroll]
      for (int i1 = 0; i1 < Input.ArrayImageLength; i1++)
      {
         if (Block.Masks[i1] == 1)
         {
            float2 D = Input.ArrayImages[i1] - Mean;
            SigmaVec += (D * D);
         }
      }

      // Compute the Trace (T): (xx / N) + (yy / N).
      float Tr = dot(SigmaVec, SigmaN);

      // Compute the Mean's Squared Euclidian Distance: M^T*M
      float M = dot(Mean, Mean);

      // Coefficient of Variance.
      // We removed the sqrt(x) because the result gets cancelled-out in GetLorentzian1D_Fast(x)
      float CoV_Sq = (abs(M) > 0.0) ? Tr / M : 0.0;

      // Fit the CoV into a Lorentzian approximation.
      Block.Influence = GetLorentzian1D_Fast(CoV_Sq, 1.0, Input.GVariance_Sq);
   }

   float2 GetSelfBilateralUpsample_FLT2(
      sampler Image, // Low-res motion vectors (e.g., 1/2 size)
      sampler Guide, // High-res structural guide (e.g., full size)
      float2 Tex
   )
   {
      const int SideWindowsCount = 8;

      // Create the data struct that we will use accross multiple functions.
      SharedData_SideWindow_Bilateral SharedData;
      GetSharedData_SideWindow_Bilateral(Image, Guide, Tex, SharedData);

      // Initialize our side windows
      SideWindow_Bilateral SideWindows[SideWindowsCount];
      SideWindows[0].Masks = { 1, 1, 0,  1, 1, 0,  0, 0, 0 }; // NW
      SideWindows[0].Size = SharedData.SideWindowSize_Corner;
      SideWindows[1].Masks = { 0, 1, 1,  0, 1, 1,  0, 0, 0 }; // NE
      SideWindows[1].Size = SharedData.SideWindowSize_Corner;
      SideWindows[2].Masks = { 0, 0, 0,  1, 1, 0,  1, 1, 0 }; // SW
      SideWindows[2].Size = SharedData.SideWindowSize_Corner;
      SideWindows[3].Masks = { 0, 0, 0,  0, 1, 1,  0, 1, 1 }; // SE
      SideWindows[3].Size = SharedData.SideWindowSize_Corner;
      SideWindows[4].Masks = { 1, 1, 1,  1, 1, 1,  0, 0, 0 }; // N
      SideWindows[4].Size = SharedData.SideWindowSize_Cardinal;
      SideWindows[5].Masks = { 0, 0, 0,  1, 1, 1,  1, 1, 1 }; // S
      SideWindows[5].Size = SharedData.SideWindowSize_Cardinal;
      SideWindows[6].Masks = { 1, 1, 0,  1, 1, 0,  1, 1, 0 }; // W
      SideWindows[6].Size = SharedData.SideWindowSize_Cardinal;
      SideWindows[7].Masks = { 0, 1, 1,  0, 1, 1,  0, 1, 1 }; // E
      SideWindows[7].Size = SharedData.SideWindowSize_Cardinal;

      /*
         Calculate the variance-weighted Side Window filter. This may sound strange, but it works better than the regular min(x) method.

         While Google's enterprise-class clanker suggested this method, I did my discernment and revised it to work like do CBloom's Karis averaging. In layman's terms, a Karis average means "we will add 4 things together: darken the very-bright things and keep the not-very-bright-things the same". The "thing" is either a single pixel (for a Full Karis Average) or a sum of pixels (for a Partial Karis Average). We use the Karis average to prevent pulsating regions when downsampling.

         What about motion vectors? Instead of measuring the sum of pixel brightness to infer pulsating areas, we use the sum of pixel variances.
      */

      float2 WindowMean = 0.0;
      float SumInfluence = 0.0;

      [unroll]
      for (int i0 = 0; i0 < SideWindowsCount; i0++)
      {
         GetSideWindow_Bilateral(SharedData, SharedData.SideWindowMeans[i0], SideWindows[i0]);

         if (SideWindows[i0].SumWeight > 0.0)
         {
            // Normalize the sum.
            float2 Sum = SideWindows[i0].Sum / SideWindows[i0].SumWeight;

            // Weighted sum by influence.
            WindowMean += (Sum * SideWindows[i0].Influence);
            SumInfluence += SideWindows[i0].Influence;
         }
      }

      WindowMean = (SumInfluence > 0.0) ? WindowMean / SumInfluence : SharedData.Reference;

      return WindowMean;
   }
