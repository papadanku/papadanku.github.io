
Commenting Preprocessor Macros
==============================

In HLSL, preprocessor macros are processed before the shader code is compiled. Because macros involve direct text substitution, the placement of comments is critical. Incorrectly placed comments can lead to compilation errors or, more subtly, unexpected code generation due to improper macro expansion.

Commenting Strategies
---------------------

There are two primary methods for documenting HLSL macros: external and internal commenting.

External Commenting
^^^^^^^^^^^^^^^^^^^

The safest and most common practice is to place comments on the line preceding the ``#define`` directive. This keeps the documentation entirely separate from the macro's token stream.

.. code-block:: hlsl

   // Calculates the luminance of a color
   // @param color: The input RGBA color
   #define GET_LUMINANCE(color) (0.2126 * color.r + 0.7152 * color.g + 0.0722 * color.b)

Internal Commenting (Block Style)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If documentation must exist within the macro itself, C-style block comments (``/* ... */``) should be used. Unlike single-line comments, block comments have an explicit end-marker, which makes them safer during the expansion process.

.. code-block:: hlsl

   #define COMPLEX_MACRO(x) \
      /* This is an internal note about the operation */ \
      ((x) * (x) + 2.0f)

Common Pitfalls
^^^^^^^^^^^^^^^

.. warning::

   **Avoid single-line comments (``//``) inside macro definitions.**

Single-Line Comment Hazards
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the ``//`` syntax within a macro definition is highly dangerous. Because the preprocessor performs simple text substitution, a single-line comment can "consume" the rest of the expanded line, including any code that was intended to follow the macro call.

Consider the following incorrect implementation:

.. code-block:: hlsl

   // BAD: Single-line comment inside macro
   #define BAD_MACRO(x) x // adds two

   // When expanded:
   // float val = BAD_MACRO(5.0f) + 10.0f;
   // Expands to:
   // float val = 5.0f // adds two + 10.0f;
   // The "+ 10.0f" is now part of the comment and is ignored by the compiler.

The correct approach is to use block comments or, preferably, external documentation.

Best Practices
^^^^^^^^^^^^^^

To ensure robust and maintainable HLSL code, adhere to these rules:

* **Prefer external documentation** on the line preceding the macro.
* **Use block comments (``/* ... */``)** for any necessary internal notes.
* **Never use single-line comments (``//``)** within a macro definition.
