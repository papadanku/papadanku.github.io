# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ReadShade'
copyright = '%Y, The ReadShade Team'
author = 'The ReadShade Team'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
html_theme = "shibuya"
html_title = "ReadShade"
html_theme_options = {
    "accent_color": "lime",
    "github_url": "https://github.com/ReadShade/ReadShade",
    "nav_links": [
        {
            "title": "Contributors",
            "children": [
                {
                    "title": "BlueSkyDefender",
                    "url": "https://github.com/BlueSkyDefender",
                    "summary": "Author of SuperDepth3D, AstrayFX, and various secret projects."
                },
                {
                    "title": "papadanku",
                    "url": "https://github.com/papadanku",
                    "summary": "Hobbyist programmer. Contributor to the Project Reality game modification and CShade."
                },
                {
                    "title": "PHARTGAMES / PEZZALUCIFER",
                    "url": "https://github.com/PHARTGAMES",
                    "summary": "Developed WibbleWobble, turning your display into a window to virtual worlds."
                }
            ]
        },
        {
            "title": "ReShade Homepage",
            "url": "https://reshade.me/"
        }
    ]
}
