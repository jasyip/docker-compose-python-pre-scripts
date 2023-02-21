# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import sys
from pathlib import PurePath, Path

sys.path.insert(0, str(PurePath(__file__).parents[2]))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Docker Compose Python Pre-Scripts'
copyright = '2023, Jason Yip'
author = 'Jason Yip'
release = (Path(__file__).parents[2] / "VERSION").read_text().strip()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
        "sphinx.ext.autodoc",
        "myst_parser",
        ]

templates_path = ['_templates']
exclude_patterns = []

suppress_warnings = ["myst.header"]
source_suffix = {
    ".md" : "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
