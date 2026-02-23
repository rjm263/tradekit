# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import re
import os
import sys
sys.path.insert(0, os.path.abspath('../../src/'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'tradekit'
copyright = '2026, rjm263'
author = 'rjm263'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
	'sphinx.ext.autodoc',                      
    'sphinx.ext.autosummary',                  
    'sphinx.ext.viewcode',                     
    'sphinx.ext.napoleon',                     
    'sphinx.ext.intersphinx',                  
	'sphinx.ext.mathjax'
]

templates_path = ['_templates']
exclude_patterns = []

add_module_names = False                        # This avoids long names like beanim.text....class_name
toc_object_entries = True                       # This allows to show the table of content-list to the right of the screen
toc_object_entries_show_parents = "hide"        # This avoids showing the parents of each class or function
# This makes that the class name goes alongs, without any parameters inside. Everything is loaded in __init__.
autodoc_class_signature = "separated"
autoclass_content = 'class'


def clean_api_titles(api_dir):
    """
    Change .rst file titles to use only the leaf name (shortest part after last dot),
    with underscores not escaped, and remove any trailing 'package' or 'module'.
    """
    for fname in os.listdir(api_dir):
        if fname.endswith(".rst"):
            path = os.path.join(api_dir, fname)
            with open(path, "r", encoding="utf8") as f:
                lines = f.readlines()
            # Sphinx-apidoc escapes _ as \_ in headings, so match either
            title_line = lines[0].strip()
            # Unescape underscores for processing
            decoded_title = title_line.replace("\\_", "_")
            # Match: e.g. beanim.text_and_organisation.blb module
            found = re.match(r"^([\w\.]+) (package|module)$", decoded_title)
            if found:
                leaf = found.group(1).split(".")[-1]
                # Write unescaped clean title
                new_title = leaf + "\n"
                lines[0] = new_title
                lines[1] = "=" * len(leaf) + "\n"
                with open(path, "w", encoding="utf8") as f:
                    f.writelines(lines)


clean_api_titles(".")

# To remove documentation on functions that do not belong to the package

def skip_inherited_members(app, what, name, obj, skip, options):
    if hasattr(obj, "__objclass__") and obj.__objclass__ is not None:
        currentclass = options.get("class", None)
        print(f"Checking {name}: objclass={obj.__objclass__.__name__} currentclass={currentclass}")
        if currentclass and obj.__objclass__.__name__ != currentclass:
            print(f"Skipping {name} because inherited")
            return True
    return skip


def setup(app):
    app.connect("autodoc-skip-member", skip_inherited_members)


# This value is a list of autodoc directive flags that should be automatically applied to all autodoc directives.
autodoc_default_options = {
    'members': True,
    # And this gets rid of the __init__ so the documentation is not oversaturated.
    'exclude-members': '__weakref__, __init__'
}


# Boolean indicating whether to scan all found documents for autosummary directives,
# and to generate stub pages for each.
autosummary_generate = False

master_doc = "index"

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = False
napoleon_numpy_docstring = True

napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False

napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

html_logo = "_static/tradekit_logo.png"

html_theme_options = {
    "sidebar_hide_name": True,
}
