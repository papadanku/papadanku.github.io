
Project Reality: Shader Model 3.0 Considerations
================================================

`The Project Reality Team <https://www.realitymod.com/>`_ updated Project Reality to support Shader Model 3. The update gave Project Reality more graphical potential. This post considerations when porting shaders from Shader Model 2 to 3.

Output Register Count
---------------------

`Shader Model 2 vertex shaders have a certain number of output registers for each type of data <https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-vs-registers-vs-2-x>`__.

   :oPos: 1 position
   :oFog: 1 fog
   :oPts: 1 point-size
   :oD#: 2 vertex color
   :oT#: 8 texture coordinate

.. note::
   
   In Shader Model 3, you have 12 output registers available for any type of data.

Input Register Format
---------------------

In Shader Model 2, output registers have different levels of precision. For example, `vertex color registers, like oD#, are 8 bits of unsigned data, in the range of 0-1 in the pixel shader <https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-ps-registers-input-color>`_.

.. note::

   When you port vertex colors from Shader Model 2 to 3, you must apply ``saturate()`` to the vertex color output.

Fogging
-------

From Shader Model 3, fogging is no longer fixed-function. You must implement your fogging method in the pixel shader.
