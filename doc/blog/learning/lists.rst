
Numbered Lists: Which Way, Markdown Man?
========================================

Hello,

I haven't updated this blog in a while. I've been busy.

Should I write a new graphics article or a new theory on global demographics and sociology?

No.

Today, I'll explain why I prefer a specific numbering style for static sites.

How Markdown Handles Ordered Lists
----------------------------------

Markdown offers several ways to create numbered (ordered) lists [1]_. All these methods produce the same results:

.. code-block:: text

   1. First item
   2. Second item
   3. Third item
   4. Fourth item

.. code-block:: text

   1. First item
   1. Second item
   1. Third item
   1. Fourth item

.. code-block:: text

   1. First item
   8. Second item
   3. Third item
   5. Fourth item

.. code-block:: text

   1. First item
   2. Second item
   3. Third item
      1. Indented item
      2. Indented item
   4. Fourth item

How reStructuredText Handles List Blocks
----------------------------------------

reStructuredText provides two ways to create numbered lists, called List Blocks [2]_. Both methods produce the same results:

.. code-block:: text

   1. First item
   2. Second item
   3. Third item

      1. Indented item
      2. Indented item
      3. Indented item

.. code-block:: text

   #. First item
   #. Second item
   #. Third item

      #. Indented item
      #. Indented item
      #. Indented item

How I do List Blocks
--------------------

I use this format for Markdown:

.. code-block:: text
   :caption: My format for Markdown.

   1. First item
   1. Second item
   1. Third item
      1. First indented item
      1. Second indented item
      1. Third indented item

.. code-block:: text
   :caption: My format for reStructuredText.

   #. First item
   #. Second item
   #. Third item

      #. Indented item
      #. Indented item
      #. Indented item

Why I Made These Choices
------------------------

It's all about **reordering**. These methods prevent you from having to reorder the entire list when you insert new items.

.. code-block:: text
   :caption: Insertion scenario on Markdown.

   1. First item
   <- Inserted item
   2. Second item
   3. Third item
      1. Indented item
      <- Inserted item
      2. Indented item
   4. Fourth item

.. code-block:: text
   :caption: Insertion scenario on reStructuredText.

   1. First item
   <- Inserted item
   2. Second item
   3. Third item

      1. Indented item
      <- Inserted item
      2. Indented item
      3. Indented item

Why It Matters
--------------

These preferences might seem trivial, but the time savings compound. You save time by avoiding manual reordering, using Large Language Models to fix lists, or tweaking Regular Expression patterns to process them.

----

.. [#] https://www.markdownguide.org/basic-syntax/#ordered-lists
.. [#] https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#lists-and-quote-like-blocks
