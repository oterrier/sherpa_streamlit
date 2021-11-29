import html
from typing import List, Optional, Iterable, cast

import pandas as pd
import plac
import streamlit as st
from annotated_text import div, annotation
from collections_extended import RangeMap
from htbuilder import HtmlElement
from streamlit.uploaded_file_manager import UploadedFile

# fmt: off
from .util import get_token, get_projects, get_project_by_label, get_project, get_annotators, get_annotator_by_label, \
    has_converter, has_formatter, annotate_text, annotate_format_text, \
    annotate_binary, annotate_format_binary, LOGO

# fmt: on
FOOTER = """<span style="font-size: 0.75em">&hearts; Built with [Streamlit](https://streamlit.io/) and largerly inspired by the great [`spacy-streamlit`](https://github.com/explosion/spacy-streamlit)</span>"""


def visualize(  # noqa: C901
        default_text: str = "",
        projects: List[str] = None,
        annotators: List[str] = None,
        annotator_types: Iterable[str] = None,
        favorite_only: bool = False,
        show_project: bool = True,
        show_annotator: bool = True,
        sidebar_title: Optional[str] = None,
        sidebar_description: Optional[str] = None,
        show_logo: bool = True,
        color: Optional[str] = "#09A3D5",
        key: Optional[str] = None
) -> None:
    """Embed the full visualizer with selected components."""
    try:
        st.set_page_config(
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://www.extremelycoolapp.com/help',
                'Report a bug': "https://www.extremelycoolapp.com/bug",
                'About': "# This is a header. This is an *extremely* cool app!"
            }
        )
    except BaseException as e:  # noqa: F841
        pass
    if st.config.get_option("theme.primaryColor") != color:
        st.config.set_option("theme.primaryColor", color)

        # Necessary to apply theming
        st.experimental_rerun()

    if show_logo:
        st.sidebar.image(LOGO, use_column_width='always')
    if sidebar_title:
        st.sidebar.title(sidebar_title)
    if sidebar_description:
        st.sidebar.markdown(sidebar_description)
    # Forms can be declared using the 'with' syntax

    try:
        with st.sidebar.form(key='connect_form'):
            url_input = st.text_input(label='Sherpa URL', value="https://sherpa-sandbox.kairntech.com/")
            name_input = st.text_input(label='Name', value="")
            pwd_input = st.text_input(label='Password', value="", type="password")
            submit_button = st.form_submit_button(label='Connect')
            if submit_button:
                st.session_state['token'] = get_token(url_input, name_input, pwd_input)
    except BaseException as e:
        st.exception(e)

    annotator = None
    project = None
    url = url_input[0:-1] if url_input.endswith('/') else url_input
    try:
        if st.session_state.get('token', None) is not None:
            all_projects = get_projects(url, st.session_state.token)
            selected_projects = sorted([p['label'] for p in all_projects if projects is None or p['name'] in projects])
            st.sidebar.selectbox('Select project', selected_projects, key="project")
            if st.session_state.get('project', None) is not None:
                project = get_project_by_label(url, st.session_state.project, st.session_state.token)
                all_annotators = get_annotators(url,
                                                project,
                                                tuple(annotator_types) if annotator_types is not None else None,
                                                favorite_only,
                                                st.session_state.token) if project is not None else []
                selected_annotators = sorted(
                    [p['label'] for p in all_annotators if annotators is None or p['name'] in annotators])
                st.sidebar.selectbox('Select annotator', selected_annotators, key="annotator")
                if st.session_state.get('annotator', None) is not None:
                    annotator = get_annotator_by_label(url, project,
                                                       tuple(annotator_types) if annotator_types is not None else None,
                                                       favorite_only,
                                                       st.session_state.annotator, st.session_state.token)

            if show_project or show_annotator:
                col1, col2, = st.columns(2)
                if project is not None and show_project:
                    with col1:
                        project_exp = st.expander("Project definition (json)")
                        project_exp.json(get_project(url, project, st.session_state.token))
                    if annotator is not None and show_annotator:
                        with col2:
                            annotator_exp = st.expander("Annotator definition (json)")
                            annotator_exp.json(annotator)

            if project is not None and annotator is not None:
                doc = None
                result = None
                if has_converter(annotator):
                    uploaded_file = st.file_uploader("File to analyze", key="file_to_analyze",
                                                     accept_multiple_files=False)
                    if uploaded_file is not None:
                        uploaded_file = cast(UploadedFile, uploaded_file)
                        if uploaded_file.type.startswith('audio'):
                            st.audio(uploaded_file.getvalue(), format=uploaded_file.type, start_time=0)
                        elif uploaded_file.type.startswith('video'):
                            st.audio(uploaded_file.getvalue(), format=uploaded_file.type, start_time=0)
                            # st.video(uploaded_file.getvalue(), format=uploaded_file.type, start_time=0)
                        if has_formatter(annotator):
                            result = annotate_format_binary(url, project, annotator['name'], uploaded_file,
                                                            st.session_state.token)
                        else:
                            docs = annotate_binary(url, project, annotator['name'], uploaded_file,
                                                   st.session_state.token)
                            doc = docs[0] if docs is not None else None
                else:
                    st.text_area("Text to analyze", default_text, max_chars=10000, key="text_to_analyze")
                    if has_formatter(annotator):
                        result = annotate_format_text(url, project, annotator['name'], st.session_state.text_to_analyze,
                                                      st.session_state.token)
                    else:
                        doc = annotate_text(url, project, annotator['name'], st.session_state.text_to_analyze,
                                            st.session_state.token)
                if doc is not None:
                    col1, col2, = st.columns(2)
                    with col1:
                        st.success('Annotation successful!')
                    with col2:
                        doc_exp = st.expander("Annotated doc (json)")
                    doc_exp.json(doc)
                    visualize_annotated_doc(doc, annotator)
                if result is not None:
                    col1, col2, = st.columns(2)
                    with col1:
                        st.success('Annotation & formatting successful!')
                    with col2:
                        st.download_button(
                            label="Download result",
                            data=result.getvalue(),
                            file_name=result.name,
                            mime=result.type)
                    if result.type in ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                        visualize_table(result, annotator)
    except BaseException as e:
        st.exception(e)
    st.sidebar.markdown(
        FOOTER,
        unsafe_allow_html=True,
    )


def visualize_table(result, annotator,
                    *,
                    title: Optional[str] = "Table",
                    key: Optional[str] = None
                    ):
    if title:
        st.header(title)
    if result.type == 'text/csv':
        df = pd.read_csv(result.getvalue())
    elif result.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        df = pd.read_excel(result.getvalue())
    st.dataframe(data=df)


def visualize_annotated_doc(
        doc,
        annotator,
        *,
        title: Optional[str] = "Annotated Document",
        key: Optional[str] = None
) -> None:
    """Visualizer for named entities."""
    if title:
        st.header(title)
    categories = doc.get('categories', [])
    labels = annotator['labels']

    if categories:
        categorized = []
        for cat in categories:
            score = cat.get('score', 1.0)
            color = labels.get(cat['labelName'], {}).get('color', "#333")
            categorized.append((cat['label'], "{:.0%}".format(score), color))
            categorized.append((" ", "", ""))

        html = annotated_text(*categorized)
        st.write(html, unsafe_allow_html=True)

    annotation_map = RangeMap()
    annotations = doc.get('annotations', [])
    text = doc['text']
    if annotations:
        for a in annotations:
            annotation_map[a['start']:a['end']] = a
        start = 0
        annotated = []
        for r in annotation_map.ranges():
            if r.start > start:
                annotated.append(text[start:r.start])
            a = r.value
            color = labels.get(a['labelName'], {}).get('color', "#333")
            annotated.append((text[r.start:r.stop], a['labelName'], color))
            start = r.stop
        if start < len(text):
            annotated.append(text[start:])
    else:
        annotated = [text]

    html = annotated_text(*annotated)
    html = html.replace("\n\n", "\n")
    st.write(html, unsafe_allow_html=True)
    #
    # if show_table:
    #     data = [
    #         [str(getattr(ent, attr)) for attr in attrs]
    #         for ent in doc.ents
    #         if ent.label_ in label_select
    #     ]
    #     if data:
    #         df = pd.DataFrame(data, columns=attrs)
    #         st.dataframe(df)


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
        style="white-space: pre-wrap; overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem")

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


def main():
    pass


if __name__ == "__main__":
    plac.call(main)
