
A Pythonic 3D Engine in 1 Weekend
=================================

I spent this weekend following `Coder Space's Python 3D engine tutorial series <https://youtube.com/playlist?list=PLi77irUVkDav8GLrZSVZiPPHvVa-RjJ-o>`_. The tutorial covered the fundamentals of the OpenGL pipeline, from the CPU to the GPU.

Main Tutorial • Video 1
-----------------------

I learned about the OpenGL pipeline, starting from the CPU to the GPU. The first tutorial taught me how to…

#. Render basic geometry
#. Add a camera to a scene
#. Add Phong lighting into a scene
#. Refactor code to re-use buffer object data
#. Use Uniform transformations
#. Adopt Best practices in rendering

   - Mipmapping
   - Gamma correction

#. Load external 3D models

.. note::

   I learned that VBOs are unformatted, allocated spaces of memory that store vertex-related data. However, we can use buffer objects for purposes other than being a VBO.

SkyBox, Environment Mapping • Video 2
-------------------------------------

I created a skybox for the rendering scene. The second tutorial taught me how to…

#. Refactor code with polymorphism
#. Make cube-maps with faces
#. Replace cube-based skybox with plane-based skybox

.. note::

   Implementing a plane-based skybox was difficult, to say the least.

Shadow Mapping, PCF • Video 3
-----------------------------

I just created a smooth shadow-mapping system for objects.

Feedback
--------

As someone who wanted to learn the graphics programming fundamentals, I found this series enjoyable to follow. I believe this tutorial can reach the masses if it also covers…

- Instancing
- Deferred rendering
- Generating vertex normal and tangent

Recommendation
--------------

I recommend this tutorial for people who already have experience with Python and want to get straight to crafting graphics. Thank you, Coder Space!
