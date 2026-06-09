# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'A Shaderboy\'s Collection'
copyright = '%Y, papadanku'
author = 'papadanku'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
html_theme = "shibuya"
html_title = "A Shaderboy's Collection"
html_theme_options = {
    "accent_color": "lime",
    "github_url": "https://github.com/papadanku/papadanku.github.io",
    "nav_links": [
        {
            "title": "Projects",
            "children": [
                {
                    "title": "CShade",
                    "url": "https://github.com/papadanku/CShade",
                    "summary": "A ReShade shader library containing various effects."
                },
                {
                    "title": "ReadShade",
                    "url": "https://github.com/ReadShade/ReadShade",
                    "summary": "A documentation site for ReShade. Written with agentic AI."
                },
                {
                    "title": "ShaderCells",
                    "url": "https://github.com/papadanku/ShaderCells",
                    "summary": "Resource files for AI agents for learning ReShadeFX and developing ReShadeFX shaders."
                },
                {
                    "title": "Skills",
                    "url": "https://github.com/papadanku/skills",
                    "summary": "Agentic AI skills that I use for my projects (ReShade, Project Reality, YouTube)."
                }
            ]
        }
    ]
}