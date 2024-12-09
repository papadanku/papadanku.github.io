
.. toctree::
   :glob:
   :titlesonly:
   :hidden:

   source/*/index

Portfolio
=========

Programming
-----------

Tools
^^^^^

I mainly use open-source software for my development.

Programming Languages
   :General: C#, Python
   :Markup: Markdown, reStructuredText
   :Shaders: High Level Shading Language \(HLSL\), OpenGL Shading Language \(GLSL\)
   :Utility: PowerShell
   :Learning: Rust

Version Control
   :Git: GitHub, GitLab
   :Subversion: TortoiseSVN

:Source Code Editors: Notepad++, Visual Studio Code, PyCharm
:Project Management: Redmine
:Documentation Generators: MkDocs, Sphinx
:Research and Development: Zotero, Logseq, draw.io
:Other: PowerShell Terminal

Experience
^^^^^^^^^^

Project Reality: Battlefield 2
""""""""""""""""""""""""""""""

:Date: 2021 - Present
:Website: https://www.realitymod.com/

I am a developer for the Project Reality: Battlefield 2 \(PR: BF2\).

Teamwork
   - Communicated with other developers on new features.
   - Helped new contributors get started with development.
   - Posted development blogs to update the player community on the game's progress.

Repository Tool Usage
   - Redmine to track changes and updates
   - TortoiseSVN as version control

HLSL: Updates
   - Rewrote shader codebase to Shader Model 3.0

     - Ported shader assembly to programmable shaders
     - Ported multitexture blending passess to programmable shaders

   - Post-processing suppression
   - Thermal pixelation
   - Water reflection

HLSL: Implementations
   - 16x anisotropic filtering support
   - Complete per-pixel lighting
   - Distance-based fog
   - Logarithmic depth buffering
   - Offmap terrain procedural sampling
   - Valve Software's `Half-Lambert Lighting <https://advances.realtimerendering.com/s2006/Mitchell-ShadingInValvesSourceEngine.pdf>`_

Python: Implementations
   - Python-generated dynamic AI view distance setting
   - Reformatted codebase to fit closer to PEP\-8 standards
   - Extended bot loadout to spawn with standard **and** alternate kits
   - Randomized bot loadout kits via Python

`RealityDocs <https://gitlab.com/realitymod/public/RealityDocs>`_
   Porting the team's modding documentation into a static documentation site.

`RealityShaders <https://github.com/realitymod/RealityShaders>`_
   Maintained an open-source repository for Project Reality's updated shaders.

`RealityUDL <https://gitlab.com/realitymod/public/realityudl>`_
   Updated Project Reality's language support for Notepad++.

Projects
^^^^^^^^

ReShade Shaders
"""""""""""""""

:Date: 2020 - Present
:Repository: https://github.com/papadanku/CShade

Created **CShade**, a library of image and video processing shaders. **CShade** contains ported and in-house shaders.

:AMD FidelityFX Ports: - `FidelityFX Lens <https://gpuopen.com/manuals/fidelityfx_sdk/fidelityfx_sdk-page_techniques_lens/>`_
                       - `FidelityFX Contrast Adaptive Sharpening \(CAS\) <https://gpuopen.com/manuals/fidelityfx_sdk/fidelityfx_sdk-page_techniques_contrast-adaptive-sharpening/>`_
                       - `FidelityFX Robust Contrast Adaptive Sharpening \(RCAS\) <https://gpuopen.com/manuals/fidelityfx_sdk/fidelityfx_sdk-page_techniques_super-resolution-upscaler/#robust-contrast-adaptive-sharpening-rcas>`_
:Anti-Aliasing: - `Fast Approximate Anti-Aliasing \(FXAA\) <https://en.wikipedia.org/wiki/Fast_approximate_anti-aliasing>`_
                - `Directionally Localized Anti-Aliasing \(DLAA\) <http://www.and.intercon.ru/releases/talks/dlaagdc2011/>`_
:Camera Effects: Autoexposure, Dual-Kawase Bloom, Lens Effect, Vignette
:Color Conversions: Chromaticity Space, Polar Coordinate Space, Grayscale
:Convolutions: Gaussian Blur, Edge Detection, Sharpening
:Local Normalization: Census Transform, Local Contrast Normalization
:Motion Estimation: Hierarchical Lucas-Kanade Optical Flow
:Post-Processing: Backbuffer Blending, Letterbox
:Video Effects: Datamoshing, Motion Blur, Vector Lines

ReadShade
"""""""""

:Date: 2024 - Present

- Launched a documentation site for ReShade-related support using MkDocs.
- Collaborated with `Depth3D <https://blueskydefender.github.io/Depth3D/>`_ to create a documentation site.

PythonicEngine
""""""""""""""

:Date: 2023
:Repository: https://papadanku.github.io/PythonicEngine/

I spent the a weekend in 2023 following `Coder Space's Python 3D Engine Series <https://youtube.com/playlist?list=PLi77irUVkDav8GLrZSVZiPPHvVa-RjJ-o>`_. Here are the things I learned about.

Day 1
   - Adding geometry, basic lighting, and a camera to a scene
   - Best practices: mipmapping, gamma-correction, code refactoring
   - Fundamentals of the OpenGL pipeline, from the CPU to the GPU
   - Using ``PyGame``, ``ModernGL``, and ``PyGLM`` to make an engine
   - Differences between Vertex Buffer Objects \(VBOs\) and Vertex Array Objects \(VAOs\)

     - A VBO is a boxs with items
     - A VAO is the box's manual on how to interpret its items

Day 2
   - Code refactoring through polymorphism
   - Creating a skybox
   - Plane-based skyboxing

Day 3
   - Creating smooth shadowmapping

Day 4+
   - Using Sphinx to generate documentation for this project

----

Content Creation, Social Media Management
-----------------------------------------

Tools
^^^^^

Used various hardware and software to create content for social media channels. A mix of freemium and open-source software.

Hardware
   :Camera: Sony Alpha 6000
   :Lens: Sony SELP 1650

Software
   `OBS Studio <https://obsproject.com/>`_
      Desktop recording, media muxing

   `yt-dlp <https://github.com/yt-dlp/yt-dlp>`_
      Media downloading, media conversion

   Video Production
      - `Blender Video Sequence Editor \(2015 -> 2020\) <https://www.blender.org/features/video-editing/>`_
      - `Davinci Resolve \(2020 -> Preset\) <https://www.blackmagicdesign.com/products/davinciresolve>`_

   Media Conversion
      - `FFmpeg <https://ffmpeg.org/>`_
      - `fre:ac <https://www.freac.org/>`_

Project Reality: Battlefield 2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Date: 2023 - Present
:Website: https://www.realitymod.com/
:Discord: https://discord.com/servers/project-reality-190090455973756928
:Facebook: https://www.facebook.com/realitymod
:Instagram: https://www.instagram.com/projectrealitymod/
:YouTube: https://www.youtube.com/@ProjectRealityMod

- Engaged with the community regarding feedback on the game.
- Created short video content for promoting Project Reality's development.

  Short 1
    - https://www.facebook.com/realitymod/videos/2024-update-reveal-1-shorts/355546420818308/
    - https://www.instagram.com/projectrealitymod/reel/C4nDvMzMEBM/
    - https://www.youtube.com/shorts/CtcVkypMKLE

  Short 2
    - https://www.facebook.com/realitymod/videos/2024-update-reveal-2-shorts/1612029272964840/
    - https://www.instagram.com/projectrealitymod/reel/C5YIZiNBViH/
    - https://www.youtube.com/shorts/1mmFA_XHZg0

Personal Social Media
^^^^^^^^^^^^^^^^^^^^^

:Date: 2022 - Present
:YouTube: https://www.youtube.com/@papadanku
:Instagram: https://www.instagram.com/paulinyourwall/

- Maintained a YouTube page for promotional and personal videos.
- Used a note-based template system through `Logseq <https://logseq.com/>`_ to streamline filling out information for video content.
- Engaged with the audience and reflected feedback.
- Used YouTube Analytics to monitor audience data.
