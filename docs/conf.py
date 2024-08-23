"""Configuration file for the Sphinx documentation builder."""

#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
from datetime import date

# -- Path Setup --------------------------------------------------------------
from os.path import abspath, dirname
from pathlib import Path

from aind_watchdog_service import __version__ as package_version

INSTITUTE_NAME = "Allen Institute for Neural Dynamics"
SOURCE_ROOT = "https://github.com/AllenNeuralDynamics/aind-watchdog-service/tree/main/src/"  # noqa: E501

current_year = date.today().year

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = Path(dirname(dirname(dirname(abspath(__file__))))).name
copyright = f"{current_year}, {INSTITUTE_NAME}"
author = INSTITUTE_NAME
release = package_version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx.ext.linkcode",
    "sphinx_mdinclude",
]


templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_title = "aind-watchdog-service"
html_favicon = "_static/favicon.ico"
html_theme_options = {
    "light_logo": "light-logo.svg",
    "dark_logo": "dark-logo.svg",
}

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = False


# -- Options for linkcode extension ------------------------------------------
def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    if not info["module"]:
        return None
    filename = info["module"].replace(".", "/")
    return f"{SOURCE_ROOT}/{filename}.py"


def copy_assets(src: os.PathLike, dst: os.PathLike) -> None:
    """Copy assets from the source directory to the destination directory."""
    import shutil

    if Path(src).is_dir():
        if Path(dst).is_dir():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        raise ValueError(f"Source directory {src} does not exist.")


copy_assets(Path("../assets"), Path("./_build/html/assets"))
