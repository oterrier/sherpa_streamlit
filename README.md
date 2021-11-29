# sherpa_streamlit

[![license](https://img.shields.io/github/license/oterrier/sherpa_streamlit)](https://github.com/oterrier/sherpa_streamlit/blob/master/LICENSE)
[![tests](https://github.com/oterrier/sherpa_streamlit/workflows/tests/badge.svg)](https://github.com/oterrier/sherpa_streamlit/actions?query=workflow%3Atests)
[![codecov](https://img.shields.io/codecov/c/github/oterrier/sherpa_streamlit)](https://codecov.io/gh/oterrier/sherpa_streamlit)
[![docs](https://img.shields.io/readthedocs/sherpa_streamlit)](https://sherpa_streamlit.readthedocs.io)
[![version](https://img.shields.io/pypi/v/sherpa_streamlit)](https://pypi.org/project/sherpa_streamlit/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sherpa_streamlit)](https://pypi.org/project/sherpa_streamlit/)

Kairntech Sherpa building blocks for Streamlit apps

This package contains utilities for visualizing and building interactive [Kairntech](https://kairntech.com) Sherpa-powered apps with
[Streamlit](https://streamlit.io). It includes various building blocks you can
use in your own Streamlit app, like visualizers for **named entities**, **text classification**, and more.

## Installation

You can simply `pip install sherpa-streamlit`.

## Quickstart

The package includes building blocks that call into Streamlit and set up all the required elements for you. You can either use the individual components directly and combine them with other elements in your app, or call the visualize function to embed the whole visualizer.

Put the following example code in a file.
```
# streamlit_app.py
import sherpa_streamlit

default_text = "Sundar Pichai is the CEO of Google."
sherpa_streamlit.visualize(default_text)
```
You can then run your app with `streamlit run streamlit_app.py`. The app should pop up in your web browser.

## Developing

### Pre-requesites

You will need to install `flit` (for building the package) and `tox` (for orchestrating testing and documentation building):

```
python3 -m pip install flit tox
```

Clone the repository:

```
git clone https://github.com/oterrier/sherpa_streamlit
```

### Running the test suite

You can run the full test suite against all supported versions of Python (3.8) with:

```
tox
```

### Building the documentation

You can build the HTML documentation with:

```
tox -e docs
```

The built documentation is available at `docs/_build/index.html.
