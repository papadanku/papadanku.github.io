
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
   \end{bmatrix}

.. math::

   G_y(i,j) = \begin{bmatrix}
   -1 & -2 & -1 \\
   0 & 0 & 0 \\
   +1 & +2 & +1 \\
   \end{bmatrix}

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

Source Code
-----------

.. code-block:: hlsl

   struct Sobel
   {
      float4 Gx;
      float4 Gy;
   };

   Sobel GetSobel(sampler SampleImage, float2 Tex, float2 PixelSize)
   {
      Sobel Output;
      float4 A = tex2D(SampleImage, Tex + (float2(-0.5, 0.5) * PixelSize));
      float4 B = tex2D(SampleImage, Tex + (float2(0.5, 0.5) * PixelSize));
      float4 C = tex2D(SampleImage, Tex + (float2(-0.5, -0.5) * PixelSize));
      float4 D = tex2D(SampleImage, Tex + (float2(0.5, -0.5) * PixelSize));
      Output.Gx = (B + D) - (A + C);
      Output.Gy = (A + B) - (C + D);
      return Output;
   }
