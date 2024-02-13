# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "OpenGSQ Python"
copyright = "2024, OpenGSQ, BattlefieldDuck"
author = "OpenGSQ, BattlefieldDuck"
release = "2.3.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_rtd_theme", "sphinx.ext.autodoc", "sphinx_docsearch"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autodoc_member_order = "bysource"

docsearch_app_id = "Z4FH0B65P0"
docsearch_api_key = "703d26db3f2af38cbcb3b92d79a048bc"
docsearch_index_name = "python-opengsq"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_favicon = "favicon.ico"
html_static_path = ["_static"]

# Enabling the extension only when building on GitHub Actions
if os.getenv("GITHUB_ACTIONS"):
    extensions.append("sphinxcontrib.googleanalytics")
    googleanalytics_id = "G-GLNNDPSR1B"
