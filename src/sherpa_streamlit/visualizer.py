from typing import List, Optional, Iterable, cast

import pandas as pd
import plac
import streamlit as st
import streamlit.components.v1 as components
from annotated_text import annotation
from collections_extended import RangeMap
from streamlit.uploaded_file_manager import UploadedFile

# fmt: off
from .util import get_token, get_projects, get_project_by_label, get_project, get_annotators, get_annotator_by_label, \
    has_converter, has_formatter, annotate_text, annotate_format_text, \
    annotate_binary, annotate_format_binary, LOGO, clean_html, clean_annotation, annotated_text, annotate_format_json, \
    annotate_json, get_sample_doc

# fmt: on
FOOTER = """<span style="font-size: 0.75em">&hearts; Built with [Streamlit](https://streamlit.io/) and largerly inspired by the great [`spacy-streamlit`](https://github.com/explosion/spacy-streamlit)</span>"""


def visualize(  # noqa: C901
        default_text: str = "",
        projects: List[str] = None,
        annotators: List[str] = None,
        annotator_types: Iterable[str] = None,
        favorite_only: bool = False,
        sample_doc: bool = True,
        show_connection: bool = True,
        show_project: bool = False,
        show_annotator: bool = False,
        show_json: bool = False,
        project_selector_title: str = "Select project",
        annotator_selector_title: str = "Select annotator",
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
        if show_connection:
            with st.sidebar.form(key='connect_form'):
                url_input = st.text_input(label='Sherpa URL', value="https://sherpa-sandbox.kairntech.com/")
                name_input = st.text_input(label='Name', value="")
                pwd_input = st.text_input(label='Password', value="", type="password")
                submit_button = st.form_submit_button(label='Connect')
                if submit_button:
                    st.session_state['token'] = get_token(url_input, name_input, pwd_input)
        else:
            url_input = st.secrets.sherpa_credentials.url
            name_input = st.secrets.sherpa_credentials.username
            pwd_input = st.secrets.sherpa_credentials.password
            st.session_state['token'] = get_token(url_input, name_input, pwd_input)
    except BaseException as e:
        st.exception(e)

    annotator = None
    project = None
    sample = None
    url = url_input[0:-1] if url_input.endswith('/') else url_input
    try:
        if st.session_state.get('token', None) is not None:
            all_projects = get_projects(url, st.session_state.token)
            selected_projects = sorted([p['label'] for p in all_projects if projects is None or p['name'] in projects])
            st.sidebar.selectbox(project_selector_title, selected_projects, key="project")
            if st.session_state.get('project', None) is not None:
                project = get_project_by_label(url, st.session_state.project, st.session_state.token)
                if sample_doc and project is not None:
                    sample = get_sample_doc(url, project, st.session_state.token)
                all_annotators = get_annotators(url,
                                                project,
                                                tuple(annotator_types) if annotator_types is not None else None,
                                                favorite_only,
                                                st.session_state.token) if project is not None else []
                selected_annotators = sorted(
                    [p['label'] for p in all_annotators if annotators is None or p['name'] in annotators])
                st.sidebar.selectbox(annotator_selector_title, selected_annotators, key="annotator")
                if st.session_state.get('annotator', None) is not None:
                    annotator = get_annotator_by_label(url, project,
                                                       tuple(annotator_types) if annotator_types is not None else None,
                                                       favorite_only,
                                                       st.session_state.annotator, st.session_state.token)

            if show_project or show_annotator:
                colp, cola, = st.columns(2)
                if project is not None and show_project:
                    with colp:
                        project_exp = st.expander("Project definition (json)")
                        project_exp.json(get_project(url, project, st.session_state.token))
                    if annotator is not None and show_annotator:
                        with cola:
                            annotator_exp = st.expander("Annotator definition (json)")
                            annotator_exp.json(annotator)

            if project is not None and annotator is not None:
                doc = None
                text = None
                uploaded_file = None
                result = None
                col1, col2, = st.columns(2)
                if has_converter(annotator):
                    file_msg = f"Upload binary file ({has_converter(annotator)['name']}) to analyze"
                    text_msg = "Or input text to analyze"
                    with col1:
                        with st.form('File1'):
                            st.file_uploader(file_msg, key="file_to_analyze", accept_multiple_files=False)
                            submittedf1 = st.form_submit_button('Process File')
                            if submittedf1:
                                uploaded_file = st.session_state.get("file_to_analyze", None)
                                if uploaded_file.type.startswith('audio'):
                                    st.audio(uploaded_file.getvalue(), format=uploaded_file.type, start_time=0)
                                elif uploaded_file.type.startswith('video'):
                                    st.audio(uploaded_file.getvalue(), format=uploaded_file.type, start_time=0)
                                    # st.video(uploaded_file.getvalue(), format=uploaded_file.type, start_time=0)
                    with col2:
                        with st.form('Text2'):
                            st.text_area(text_msg, sample['text'] if sample is not None else default_text,
                                         max_chars=10000, key="text_to_analyze")
                            submittedt2 = st.form_submit_button('Process Text')
                            if submittedt2:
                                text = st.session_state.get("text_to_analyze", None)
                else:
                    text_msg = "Input text to analyze"
                    file_msg = "Or upload text/json file to analyze"
                    with col1:
                        with st.form('Text1'):
                            st.text_area(text_msg, sample['text'] if sample is not None else default_text,
                                         max_chars=10000, key="text_to_analyze")
                            submittedt1 = st.form_submit_button('Process Text')
                            if submittedt1:
                                text = st.session_state.get("text_to_analyze", None)
                    with col2:
                        with st.form('File2'):
                            st.file_uploader(file_msg, key="file_to_analyze", accept_multiple_files=False)
                            submittedf2 = st.form_submit_button('Process File')
                            if submittedf2:
                                uploaded_file = st.session_state.get("file_to_analyze", None)

                if uploaded_file is not None:
                    uploaded_file = cast(UploadedFile, uploaded_file)
                    if has_converter(annotator):
                        if has_formatter(annotator):
                            result = annotate_format_binary(url, project, annotator['name'], uploaded_file,
                                                            st.session_state.token)
                        else:
                            docs = annotate_binary(url, project, annotator['name'], uploaded_file,
                                                   st.session_state.token)
                            doc = docs[0] if docs is not None else None
                    else:
                        if 'json' in uploaded_file.type:
                            if has_formatter(annotator):
                                result = annotate_format_json(url, project, annotator['name'], uploaded_file,
                                                              st.session_state.token)
                            else:
                                docs = annotate_json(url, project, annotator['name'], uploaded_file,
                                                     st.session_state.token)
                                doc = docs[0] if docs is not None else None
                        else:
                            text = uploaded_file.getvalue().decode("utf-8")
                if text is not None:
                    if has_formatter(annotator):
                        result = annotate_format_text(url, project, annotator['name'], text,
                                                      st.session_state.token)
                    else:
                        doc = annotate_text(url, project, annotator['name'], text,
                                            st.session_state.token)

                if doc is not None:
                    col1, col2, = st.columns(2)
                    with col1:
                        st.success('Annotation successful!')
                    if show_json:
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
            name = cat['labelName']
            score = cat.get('score', 1.0)
            color = labels.get(name, {}).get('color', "#333")
            categorized.append(annotation(cat.get('label', name), "{:.0%}".format(score), color))
            categorized.append(" ")

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
                annotated.append(clean_html(text[start:r.start]))
            a = r.value
            name = a['labelName']
            color = labels.get(name, {}).get('color', "#333")
            annotated.append(clean_annotation(text[r.start:r.stop], clean_html(a.get('label', name)), color))
            start = r.stop
        if start < len(text):
            annotated.append(clean_html(text[start:]))
    else:
        annotated = [text]

    html = annotated_text(*annotated)
    # html = html.replace("\n", "<br/>")
    components.html(html, width=800, height=800, scrolling=True)
    # st.write(html, unsafe_allow_html=True)


def main():
    pass


if __name__ == "__main__":
    plac.call(main)
