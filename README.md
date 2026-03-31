# ReadShade

## Project Overview

ReadShade is a Sphinx documentation project that provides a neutral and simple platform for sharing knowledge about ReShade, Depth3D, emulators, games, and hardware. It serves as a comprehensive resource for users and developers looking to enhance their gaming experience through post-processing effects and optimization techniques.

## Project Structure

The documentation is organized into thematic domains within the `source/` directory:

- **ReShade General**: Covers optimization, DXVK integration, and engine-specific tweaks.
- **Learning**: Focuses on ReShadeFX shader development with step-by-step guides for creating and understanding shaders.
- **Software**: Includes detailed guides for emulators (PCSX2), ReShade add-ons (ShaderToggler, REST), and comprehensive documentation for the CShade shader collection.
- **Third-Party**: Features documentation for external tools like Depth3D and WibbleWobble, along with specialized hardware guides for Viture and Super Reality (SR) devices.
- **Licensing**: Contains copyright information and software licenses relevant to the project components.

## Organization & Navigation

The project maintains a clean, hierarchical structure for easy navigation:

- **Root Index**: The `source/index.rst` file serves as the master table of contents, defining the primary sections of the documentation.
- **Domain Indices**: Each domain subdirectory uses its own `index.rst` file with automatic discovery to include all relevant articles.
- **Asset Management**: Images are stored in local `images/` subdirectories within each domain to keep content and assets logically grouped.

## Technologies Used

This project utilizes:

- **[Sphinx](https://www.sphinx-doc.org/)**: The primary engine for generating documentation.
- **[reStructuredText (.rst)](https://docutils.sourceforge.io/rst.html)**: The markup language used for writing all documentation.
- **[Shibuya Theme](https://shibuya.lepture.com/)**: A modern, clean visual theme for the generated output.
- **[Python](https://www.python.org/)**: The programming language that powers Sphinx.
- **[pip](https://pip.pypa.io/)**: The package manager for installing and maintaining project dependencies.
