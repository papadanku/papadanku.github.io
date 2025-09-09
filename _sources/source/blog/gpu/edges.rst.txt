
.. role:: hlsl(code)
   :language: hlsl

Bilinear Edge Detection on the GPU
==================================

What is Edge Detection?
-----------------------

Edge detection is a fundamental technique in image processing and computer vision. Its primary goal is to identify points in a digital image where the brightness or intensity of the image changes sharply. These sharp changes, or "edges," often correspond to the boundaries of objects, surface discontinuities, or changes in material properties. By simplifying the image into its core structural components, edge detection serves as a critical pre-processing step for more complex tasks like object recognition, tracking, and segmentation.

What is the Sobel Filter?
-------------------------

The Sobel filter is a discrete differentiation operator that computes an approximation of the gradient of the image intensity function. At each pixel in the image, the result of the Sobel operator is the corresponding gradient vector or its magnitude. The operator is based on two 3x3 convolution kernels. One kernel is used to find the horizontal gradient :math:`G_x` and the other to find the vertical gradient :math:`G_y`.

For a pixel at coordinates :math:`(i,j)`, the horizontal and vertical gradients are calculated as follows:

.. math::

   G_x(i,j) = \begin{bmatrix}
   -1 & 0 & +1 \\
   -2 & 0 & +2 \\
   -1 & 0 & +1 \\
   \end{bmatrix} \ast A

.. math::

   G_y(i,j) = \begin{bmatrix}
   +1 & +2 & +1 \\
   0 & 0 & 0 \\
   -1 & -2 & -1 \\
   \end{bmatrix} \ast A

The magnitude of the gradient at that point is then calculated as:

.. math::

   |G| = \sqrt{G_x^2 + G_y^2}

Why We Use the Sobel Filter
---------------------------

The Sobel filter is widely used due to its simplicity and computational efficiency. Its primary application is in edge detection, which is a crucial step in many computer vision tasks, including:

- **Object recognition:** Identifying the boundaries of objects.
- **Feature extraction:** Detecting key points and features in an image.
- **Image segmentation:** Dividing an image into multiple segments.
- **Robotics and autonomous systems:** Enabling machines to understand their environment by detecting edges of obstacles and paths.

Optimizing with Bilinear Interpolation
--------------------------------------

Traditionally, applying a Sobel filter on a GPU requires eight separate texture fetches for each pixel: one for each of its neighbors. However, we can achieve significant optimization by utilizing the linearity of the Sobel kernels and the advanced features of modern GPU hardware, particularly bilinear interpolation.

The key insight here is that the horizontal and vertical kernels are both separable and linear. This property of the Sobel filter allows us to combine the operations. Instead of sampling all eight individual pixels, we can sample just four strategic points located between the centers of adjacent pixels. The GPU's built-in bilinear interpolation function will automatically fetch and combine the four nearest texels.

Consider the four sampling points: :hlsl:`A`, :hlsl:`B`, :hlsl:`C`, and :hlsl:`D`, which are located at the corners of a conceptual "pixel" area. Bilinear interpolation at these points provides the weighted sum of the underlying pixel values necessary for calculating the Sobel gradients.

For a normalized texture coordinate :hlsl:`Tex`, and a pixel size :hlsl:`PixelSize`:

- Sample :hlsl:`A` is taken at :hlsl:`Tex + (float2(-0.5, 0.5) * PixelSize)`
- Sample :hlsl:`B` is taken at :hlsl:`Tex + (float2(0.5, 0.5) * PixelSize)`
- Sample :hlsl:`C` is taken at :hlsl:`Tex + (float2(-0.5, -0.5) * PixelSize)`
- Sample :hlsl:`D` is taken at :hlsl:`Tex + (float2(0.5, -0.5) * PixelSize)`

By strategically combining these four interpolated samples, we can derive the complete Sobel gradients. The horizontal gradient :math:`Ix` is calculated by adding the values of samples :hlsl:`B` and :hlsl:`D` and then subtracting the sum of samples :hlsl:`A` and :hlsl:`C`. Similarly, the vertical gradient :math:`Iy` is determined by adding samples :hlsl:`A` and :hlsl:`B` and subtracting the sum of samples :hlsl:`C` and :hlsl:`D`.

This method reduces the number of texture fetches from nine to four, resulting in a significant performance improvement, particularly in pixel-heavy fragment shaders. This technique is highly efficient and widely used for real-time edge detection in graphics applications.

.. code-block:: hlsl
   :caption: Bilinear Sobel Filter

   void GetBilinearSobel(in sampler SampleImage, in float2 Tex, in float2 PixelSize, out float4 Gx, out float4 Gy)
   {
      const float P = 1.0 / 2.0;

      float4 SobelTex = Tex.xyxy + (float4(-P, -P, P, P) * PixelSize.xyxy);
      float4 NW = tex2D(SampleImage, SobelTex.xw); // <-0.5, +0.5>
      float4 NE = tex2D(SampleImage, SobelTex.zw); // <+0.5, +0.5>
      float4 SW = tex2D(SampleImage, SobelTex.xy); // <-0.5, -0.5>
      float4 SE = tex2D(SampleImage, SobelTex.zy); // <+0.5, -0.5>

      Gx = (NE + SE) - (NW + SW);
      Gy = (NW + NE) - (SW + SE);
   }

Bilinear Prewitt and Scharr Kernels
-----------------------------------

The bilinear optimization technique is not confined to the Sobel filter; it can also be applied to other common edge detection kernels, such as the Prewitt and Scharr filters. This approach involves scaling the spread of the bilinear fetches and normalizing the weighted sum.

Prewitt Kernel
^^^^^^^^^^^^^^

The Prewitt operator is a simpler, unweighted version of the Sobel filter. It applies a constant weight of 1 to all pixels in the 3x3 kernel, in contrast to the Sobel filter, which assigns a weight of 2 to the central row and column. As a result, the same four-fetch bilinear method can be directly applied and seen as a bilinear approximation of the Prewitt kernel.

.. math::

   G_x(i,j) = \begin{bmatrix}
   -1 & 0 & +1 \\
   -1 & 0 & +1 \\
   -1 & 0 & +1 \\
   \end{bmatrix} \ast A

.. math::

   G_y(i,j) = \begin{bmatrix}
   +1 & +1 & +1 \\
   0 & 0 & 0 \\
   -1 & -1 & -1 \\
   \end{bmatrix} \ast A


.. code-block:: hlsl
   :caption: Bilinear Prewitt Filter

   void GetBilinearPrewitt(in sampler SampleImage, in float2 Tex, in float2 PixelSize, out float4 Gx, out float4 Gy)
   {
      const float P = 2.0 / 3.0;
      const float Normalize = 3.0 / 4.0;

      float4 PrewittTex = Tex.xyxy + (float4(-P, -P, P, P) * PixelSize.xyxy);
      float4 NW = tex2D(SampleImage, PrewittTex.xw); // <-0.625, +0.625>
      float4 NE = tex2D(SampleImage, PrewittTex.zw); // <+0.625, +0.625>
      float4 SW = tex2D(SampleImage, PrewittTex.xy); // <-0.625, -0.625>
      float4 SE = tex2D(SampleImage, PrewittTex.zy); // <+0.625, -0.625>

      Gx = ((NE + SE) - (NW + SW)) * Normalize;
      Gy = ((NW + NE) - (SW + SE)) * Normalize;
   }

Scharr Kernel
^^^^^^^^^^^^^

The Scharr operator offers a more rotationally symmetric alternative to the Sobel filter, which can enhance the accuracy of edge detection. Its kernel coefficients are optimized to achieve better rotational symmetry than those of the Sobel operator.

.. math::

   G_x(i,j) = \begin{bmatrix}
   -3 & 0 & +3 \\
   -10 & 0 & +10 \\
   -3 & 0 & +3 \\
   \end{bmatrix} \ast A

.. math::

   G_y(i,j) = \begin{bmatrix}
   +3 & +10 & +3 \\
   0 & 0 & 0 \\
   -3 & -10 & -3 \\
   \end{bmatrix} \ast A

To approximate the Scharr kernel with four bilinear fetches, we have to adjust the sampling offsets hlsl:`Tex` to a specific spread that corresponds to the kernel's weights. Additionally, the final result needs to be normalized to reflect the different coefficient values. These adjustments showcase the versatility of the bilinear approach in approximating a variety of linear kernels using a fixed number of texture fetches.

.. code-block:: hlsl
   :caption: Bilinear Scharr Filter

   void GetBilinearScharr(in sampler SampleImage, in float2 Tex, in float2 PixelSize, out float4 Gx, out float4 Gy)
   {
      const float P = 3.0 / 8.0;
      const float Normalize = 4.0 / 3.0;

      float4 ScharrTex = Tex.xyxy + (float4(-P, -P, P, P) * PixelSize.xyxy);
      float4 NW = tex2D(SampleImage, ScharrTex.xw); // <-0.375, +0.375>
      float4 NE = tex2D(SampleImage, ScharrTex.zw); // <+0.375, +0.375>
      float4 SW = tex2D(SampleImage, ScharrTex.xy); // <-0.375, -0.375>
      float4 SE = tex2D(SampleImage, ScharrTex.zy); // <+0.375, -0.375>

      Gx = ((NE + SE) - (NW + SW)) * Normalize;
      Gy = ((NW + NE) - (SW + SE)) * Normalize;
   }
