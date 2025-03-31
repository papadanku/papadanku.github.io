
A Pythonic 3D Engine in 1 Weekend
=================================

This weekend, I followed `Coder Space's Python 3D engine tutorial series <https://youtube.com/playlist?list=PLi77irUVkDav8GLrZSVZiPPHvVa-RjJ-o>`_, which covers the fundamentals of the OpenGL pipeline, from CPU to GPU.

Video 1: Main Tutorial
----------------------

I learned about the OpenGL pipeline, from CPU to GPU. The first tutorial demonstrated how to:

1.  Render basic geometry.
2.  Implement a scene camera.
3.  Add Phong lighting to a scene.
4.  Refactor code for buffer object data reuse.
5.  Apply uniform transformations.
6.  Adopt rendering best practices:

    - Mipmapping
    - Gamma correction

7.  Load external 3D models.

.. note::

   I learned that Vertex Buffer Objects \(VBOs\) are unformatted, allocated memory spaces for vertex-related data. However, buffer objects can serve purposes beyond VBOs.

Video 2: Skybox and Environment Mapping
---------------------------------------

I created a skybox for the rendering scene. The second tutorial demonstrated how to:

1.  Refactor code using polymorphism.
2.  Generate cube maps from faces.
3.  Implement a plane-based skybox, replacing the cube-based version.

.. note::

   Implementing a plane-based skybox presented significant challenges.

Video 3: Shadow Mapping with PCF
--------------------------------

I implemented a smooth shadow-mapping system with Percentage-Closer Filtering \(PCF\).

Feedback
--------

As someone eager to learn graphics programming fundamentals, I found this series highly engaging. To further broaden its appeal, consider including tutorials on:

* Instancing
* Deferred rendering
* Vertex normal and tangent generation

Recommendation
--------------

I recommend this tutorial for individuals with Python experience who wish to dive directly into graphics development. Thank you, Coder Space!
