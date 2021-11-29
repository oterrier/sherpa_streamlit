from pathlib import Path
from typing import Tuple
import requests
import streamlit as st
from PIL import Image
from multipart.multipart import parse_options_header
from streamlit.uploaded_file_manager import UploadedFile, UploadedFileRec


# @st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_token(server: str, user: str, password: str):
    url = f"{server}/api/auth/login"
    auth = {"email": user, "password": password}
    r = requests.post(url, json=auth, params={'projectAccessMode': 'chmod'},
                      headers={'Content-Type': "application/json", 'Accept': "application/json"},
                      verify=False)
    if r.ok:
        json_response = r.json()
        if 'access_token' in json_response:
            token = json_response['access_token']
            return token
        else:
            return
    else:
        r.raise_for_status()


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_projects(server: str, token: str):
    url = f"{server}/api/projects"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    if r.ok:
        return r.json()
    else:
        r.raise_for_status()


def get_project_by_label(server: str, label: str, token: str):
    projects = get_projects(server, token)
    for p in projects:
        if p['label'] == label:
            return p['name']
    return None


def get_project(server: str, name: str, token: str):
    projects = get_projects(server, token)
    for p in projects:
        if p['name'] == name:
            return p
    return None


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_annotators(server: str, project: str, annotator_types: Tuple[str], favorite_only: bool, token: str):
    # st.write("get_annotators(", server, ", ", project, ", ", annotator_types,", ", favorite_only, ")")
    url = f"{server}/api/projects/{project}/annotators_by_type"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    annotators = []
    if r.ok:
        json_response = r.json()
        # st.write("get_annotators(", server, ", ", project, ", ", annotator_types, ", ", favorite_only,
        #          "): json_response=", str(json_response))
        for type, ann_lst in json_response.items():
            for annotator in ann_lst:
                # st.write("get_annotators(", server, ", ", project, ", ", annotator_types, ", ", favorite_only,
                #          "): annotator=", str(annotator))
                if annotator_types is None or type in annotator_types:
                    if not favorite_only or annotator.get('favorite', False):
                        annotator['type'] = type
                        annotators.append(annotator)
    else:
        r.raise_for_status()
    return annotators


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_labels(server: str, project: str, token: str):
    url = f"{server}/api/projects/{project}/labels"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    labels = {}
    if r.ok:
        json_response = r.json()
        for lab in json_response:
            labels[lab['name']] = lab
    return labels


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_annotator_by_label(server: str, project: str, annotator_types: Tuple[str], favorite_only: bool,
                           label: str, token: str):
    # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, ")")
    annotators = get_annotators(server, project, annotator_types, favorite_only, token)
    # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): annotators=", str(annotators))
    for i, ann in enumerate(annotators):
        # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): p=", str(p))
        if ann['label'] == label:
            all_labels = {}
            if ann['type'] == 'plan':
                plan = get_plan(server, project, ann['name'], token)
                if plan is not None:
                    ann.update(plan)
                    definition = plan['parameters']
                    for step in definition['pipeline']:
                        # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): step=", str(step))
                        if step.get('projectName', project) != project:
                            step_labels = get_labels(server, step['projectName'], token)
                            all_labels.update(step_labels)
            project_labels = get_labels(server, project, token)
            all_labels.update(project_labels)
            ann['labels'] = all_labels
            return ann
    return None


def has_converter(ann):
    result = 'converter' in ann['parameters'] if ann['type'] == 'plan' else False
    return result


def has_formatter(ann):
    result = 'formatter' in ann['parameters'] if ann['type'] == 'plan' else False
    return result


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_plan(server: str, project: str, name: str, token: str):
    url = f"{server}/api/projects/{project}/plans/{name}"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    if r.ok:
        return r.json()
    else:
        r.raise_for_status()


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def annotate_text(server: str, project: str, annotator: str, text: str, token: str):
    # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, ")")
    url = f"{server}/api/projects/{project}/annotators/{annotator}/_annotate"
    # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, "), url=", url)
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "text/plain", 'Accept': "application/json"}
    r = requests.post(url, data=text.encode(encoding="utf-8"), headers=headers, verify=False, timeout=1000)
    if r.ok:
        doc = r.json()
        # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, "), doc=", str(doc))
        return doc
    else:
        r.raise_for_status()


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def annotate_format_text(server: str, project: str, annotator: str, text: str, token: str):
    # st.write("annotate_format_text(", server, ", ", project, ", ", annotator, ")")
    url = f"{server}/api/projects/{project}/plans/{annotator}/_annotate_format_text"
    # st.write("annotate_format_text(", server, ", ", project, ", ", annotator, "), url=", url)
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "text/plain", 'Accept': "application/octet-stream"}
    r = requests.post(url, data=text.encode(encoding="utf-8"), headers=headers, verify=False, timeout=1000)
    if r.ok:
        data = r.content
        type = r.headers.get('Content-Type', 'application/octet-stream')
        filename = "file"
        if 'Content-Disposition' in r.headers:
            content_type, content_parameters = parse_options_header(r.headers['Content-Disposition'])
            if b'filename' in content_parameters:
                filename = content_parameters[b'filename'].decode("utf-8")
        return UploadedFile(UploadedFileRec(id=0, name=filename, type=type, data=data))
    else:
        r.raise_for_status()


def annotate_binary(server: str, project: str, annotator: str, datafile: UploadedFile, token: str):
    url = f"{server}/api/projects/{project}/plans/{annotator}/_annotate_binary"
    headers = {'Authorization': 'Bearer ' + token}
    files = {
        'file': (datafile.name, datafile.getvalue(), datafile.type)
    }
    r = requests.post(url, files=files, headers=headers, verify=False, timeout=1000)
    if r.ok:
        docs = r.json()
        # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, "), doc=", str(doc))
        return docs
    else:
        r.raise_for_status()


def annotate_format_binary(server: str, project: str, annotator: str, datafile: UploadedFile, token: str):
    url = f"{server}/api/projects/{project}/plans/{annotator}/_annotate_format_binary"
    headers = {'Authorization': 'Bearer ' + token}
    files = {
        'file': (datafile.name, datafile.getvalue(), datafile.type)
    }
    r = requests.post(url, files=files, headers=headers, verify=False, timeout=1000)
    if r.ok:
        data = r.content
        type = r.headers.get('Content-Type', 'application/octet-stream')
        filename = "file"
        if 'Content-Disposition' in r.headers:
            content_type, content_parameters = parse_options_header(r.headers['Content-Disposition'])
            if b'filename' in content_parameters:
                filename = content_parameters[b'filename'].decode("utf-8")
        return UploadedFile(UploadedFileRec(id=0, name=filename, type=type, data=data))
    else:
        r.raise_for_status()


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_logo():
    srcdir = Path(__file__).parent
    image = Image.open(srcdir / 'kairntech-1000-Blockmark.png')
    return image


def get_html(html: str):
    """Convert HTML so it can be rendered."""
    WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
    # Newlines seem to mess with the rendering
    html = html.replace("\n", " ")
    return WRAPPER.format(html)


LOGO = get_logo()

# def main():
#     url_input = "https://sherpa-sandbox.kairntech.com/"
#     url = url_input[0:-1] if url_input.endswith('/') else url_input
#     projects = None
#     annotators = None
#     annotator_types = None
#     token = get_token(url, "", "")
#     all_projects = get_projects(url, token)
#     selected_projects = sorted([p['label'] for p in all_projects if projects is None or p['name'] in projects])
#     project = "Terrorisme REN"
#     project = get_project_by_label(url, project, token)
#     all_annotators = get_annotators(url,
#                                     project,
#                                     tuple(annotator_types) if annotator_types is not None else None,
#                                     False,
#                                     token) if project is not None else []
#     selected_annotators = sorted(
#         [p['label'] for p in all_annotators if annotators is None or p['name'] in annotators])
#
# if __name__ == "__main__":
#     plac.call(main)
