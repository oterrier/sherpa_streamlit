import html
from pathlib import Path
from typing import Tuple, List, Optional

import streamlit as st
from PIL import Image
from annotated_text import annotation
from annotated_text.util import span, rem, div, em, px
from bs4 import BeautifulSoup
from htbuilder import styles, HtmlElement
from sherpa_client.models import Document, ProjectBean


def ProjectBean_hash(self):
    return self.name


def Document_hash(self):
    return self.text


def StreamlitSherpaClient_hash(self):
    return self.client.token


def ExtendedAnnotator_hash(self):
    return (self.name, self.type)


HASH_FUNCS = {
    "sherpa_streamlit.sherpa.StreamlitSherpaClient": StreamlitSherpaClient_hash,
    "sherpa_streamlit.sherpa.ExtendedAnnotator": ExtendedAnnotator_hash,
    "sherpa_client.models.ProjectBean": ProjectBean_hash,
    "sherpa_client.models.Document": Document_hash,
}


def get_client(token: str):
    from sherpa_streamlit.sherpa import StreamlitSherpaClient

    return StreamlitSherpaClient.from_token(token)


@st.experimental_memo(suppress_st_warning=True, show_spinner=False, ttl=24 * 3600)
def get_cached_projects(token: str, debug: bool = False) -> List[ProjectBean]:
    if debug:
        st.write("Cache miss: get_cached_projects(", token, ") ran")
    return get_client(token).get_projects()


@st.experimental_memo(suppress_st_warning=True, show_spinner=False, ttl=24 * 3600)
def get_cached_sample_doc(token: str, project: str, debug: bool = False) -> Document:
    if debug:
        st.write("Cache miss: get_cached_sample_doc(", token, ",", project, ") ran")
    return get_client(token).get_sample_doc(project)


@st.experimental_memo(suppress_st_warning=True, show_spinner=False, ttl=24 * 3600)
def get_cached_annotators(
    token: str,
    project: str,
    annotator_types: Tuple[str] = None,
    favorite_only: bool = False,
    debug: bool = False,
):
    if debug:
        st.write(
            "Cache miss: get_cached_annotators(",
            token,
            ",",
            project,
            ",",
            annotator_types,
            ",",
            favorite_only,
            ") ran",
        )
    return get_client(token).get_annotators(project, annotator_types, favorite_only)


@st.experimental_memo(suppress_st_warning=True, show_spinner=False, ttl=24 * 3600)
def get_cached_annotator_by_label(
    token: str,
    project: str,
    label: str,
    annotator_types: Tuple[str] = None,
    favorite_only: bool = False,
    debug: bool = False,
):
    if debug:
        st.write(
            "Cache miss: get_cached_annotator_by_label(",
            token,
            ",",
            project,
            ",",
            label,
            ",",
            annotator_types,
            ",",
            favorite_only,
            ") ran",
        )
    annotators = get_cached_annotators(token, project, annotator_types, favorite_only)
    for ann in annotators:
        if ann.label == label:
            return ann
    return None


@st.experimental_memo(suppress_st_warning=True, show_spinner=False, ttl=24 * 3600)
def get_cached_project_by_label(
    token: str, label: str, debug: bool = False
) -> Optional[ProjectBean]:
    if debug:
        st.write("Cache miss: get_cached_project_by_label(", token, ",", label, ") ran")
    projects = get_cached_projects(token)
    for p in projects:
        if p.label == label:
            return p
    return None


@st.experimental_memo(suppress_st_warning=True)
def get_logo():
    srcdir = Path(__file__).parent
    image = Image.open(srcdir / "kairntech-1000-Blockmark.png")
    return image


def get_html(html: str):
    """Convert HTML so it can be rendered."""
    WRAPPER = """<div style="line-height: 1.75rem; letter-spacing: 0em; overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
    # Newlines seem to mess with the rendering
    html = html.replace("\n", " ")
    return WRAPPER.format(html)


def clean_annotation(body, label="", background="#ddd", color="#333", **style):
    """Build an HtmlElement span object with the given body and annotation label.

    The end result will look something like this:

        [body | label]

    Parameters
    ----------
    body : string
        The string to put in the "body" part of the annotation.
    label : string
        The string to put in the "label" part of the annotation.
    background : string
        The color to use for the background "chip" containing this annotation.
    color : string
        The color to use for the body and label text.
    **style : dict
        Any CSS you want to use to customize the containing "chip".

    Examples
    --------

    Produce a simple annotation with default colors:

    >>> annotation("apple", "fruit")

    Produce an annotation with custom colors:

    >>> annotation("apple", "fruit", background="#FF0", color="black")

    Produce an annotation with crazy CSS:

    >>> annotation("apple", "fruit", background="#FF0", border="1px dashed red")

    """

    return span(
        style=styles(
            border_style="solid",
            border_color=background,
            border_radius=rem(0.33),
            color=color,
            padding=(0, rem(0.67)),
            # border_radius=em(0.3),
            # padding=(em(0.5), em(0.1)),
            white_space="normal",
            **style,
        ),
        title=label,
    )(
        html.escape(body),
    )


def annotated_text(*args):
    """Writes test with annotations into your Streamlit app.

    Parameters
    ----------
    *args : str, tuple or htbuilder.HtmlElement
        Arguments can be:
        - strings, to draw the string as-is on the screen.
        - tuples of the form (main_text, annotation_text, background, color) where
          background and foreground colors are optional and should be an CSS-valid string such as
          "#aabbcc" or "rgb(10, 20, 30)"
        - HtmlElement objects in case you want to customize the annotations further. In particular,
          you can import the `annotation()` function from this module to easily produce annotations
          whose CSS you can customize via keyword arguments.

    Examples
    --------

    >>> annotated_text(
    ...     "This ",
    ...     ("is", "verb", "#8ef"),
    ...     " some ",
    ...     ("annotated", "adj", "#faa"),
    ...     ("text", "noun", "#afa"),
    ...     " for those of ",
    ...     ("you", "pronoun", "#fea"),
    ...     " who ",
    ...     ("like", "verb", "#8ef"),
    ...     " this sort of ",
    ...     ("thing", "noun", "#afa"),
    ... )

    >>> annotated_text(
    ...     "Hello ",
    ...     annotation("world!", "noun", color="#8ef", border="1px dashed red"),
    ... )

    """
    out = div(
        style=styles(
            line_height=rem(1.75),
            letter_spacing=em(0),
            white_space="pre-wrap",
            overflow_x="auto",
            border=px(1),
            border_color="#e6e9ef",
            border_style="solid",
            border_radius=rem(0.25),
            padding=rem(1.0),
            margin_bottom=rem(2.5),
        )
    )
    # style="line-height: 1.75rem; letter-spacing: 0em; white-space: pre-wrap; overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem")

    for arg in args:
        if isinstance(arg, str):
            out(html.escape(arg))

        elif isinstance(arg, HtmlElement):
            out(arg)

        elif isinstance(arg, tuple):
            out(annotation(*arg))

        else:
            raise Exception("Oh noes!")

    return str(out)


def clean_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


LOGO = get_logo()
