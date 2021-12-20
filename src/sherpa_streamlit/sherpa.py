import json
from typing import Any, Dict, Type, TypeVar, Union
from typing import Tuple, Sequence, List

import attr
from methodtools import lru_cache
from multipart.multipart import parse_options_header
from sherpa_client.api.annotate import annotate_format_binary_with_plan_ref, annotate_binary_with_plan_ref, \
    annotate_documents_with, \
    annotate_format_documents_with_plan_ref, annotate_format_text_with_plan_ref, annotate_text_with
from sherpa_client.api.annotators import get_annotators_by_type
from sherpa_client.api.documents import export_documents_sample
from sherpa_client.api.labels import get_labels
from sherpa_client.api.plans import get_plan
from sherpa_client.api.projects import get_projects
from sherpa_client.client import SherpaClient
from sherpa_client.models import Credentials, RequestJwtTokenProjectAccessMode, AnnotatorMultimap, WithAnnotator, \
    AnnotateFormatBinaryWithPlanRefMultipartData, InputDocument, AnnotatedDocument, NamedAnnotationPlan, Label, \
    Document, ProjectBean, AnnotationPlan
from sherpa_client.types import File, Unset, UNSET, Response
from streamlit.uploaded_file_manager import UploadedFile

T = TypeVar("T", bound="ExtendedAnnotator")


@attr.s(auto_attribs=True)
class ExtendedAnnotator:
    """ """
    name: str
    label: str
    type: str
    engine: str
    labels: Union[Unset, Dict[str, Label]] = UNSET
    favorite: Union[Unset, bool] = UNSET
    is_default: Union[Unset, bool] = UNSET
    parameters: Union[Unset, AnnotationPlan] = UNSET
    created_at: Union[Unset, str] = UNSET
    created_by: Union[Unset, str] = UNSET
    modified_by: Union[Unset, str] = UNSET
    modified_at: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        label = self.label
        type = self.type
        engine = self.engine
        if self.labels is not UNSET:
            labels = {k: v.to_dict() for k, v in self.labels.items()}
        else:
            labels = UNSET
        favorite = self.favorite
        is_default = self.is_default
        if self.parameters is not UNSET:
            parameters = self.parameters.to_dict()
        else:
            parameters = UNSET
        created_at = self.created_at
        created_by = self.created_by
        modified_by = self.modified_by
        modified_at = self.modified_at

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "label": label,
                "type": type,
                "engine": engine,
            }
        )
        if labels is not UNSET:
            field_dict["labels"] = labels
        if favorite is not UNSET:
            field_dict["favorite"] = favorite
        if is_default is not UNSET:
            field_dict["is_default"] = is_default
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if created_by is not UNSET:
            field_dict["createdBy"] = created_by
        if modified_by is not UNSET:
            field_dict["modifiedBy"] = modified_by
        if modified_at is not UNSET:
            field_dict["modifiedAt"] = modified_at

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")
        label = d.pop("label")
        engine = d.pop("engine")
        type = d.pop("type")
        labels = d.pop("labels", UNSET)
        if labels is not UNSET:
            labels = {k: Label.from_dict(v) for k, v in labels.items()}

        parameters = d.pop("parameters", UNSET)
        if parameters is not UNSET:
            parameters = AnnotationPlan.from_dict(parameters)

        created_at = d.pop("createdAt", UNSET)

        created_by = d.pop("createdBy", UNSET)

        modified_by = d.pop("modifiedBy", UNSET)

        modified_at = d.pop("modifiedAt", UNSET)

        favorite = d.pop("favorite", UNSET)

        extended_annotator = cls(
            name=name,
            label=label,
            engine=engine,
            type=type,
            labels=labels,
            parameters=parameters,
            created_at=created_at,
            created_by=created_by,
            modified_by=modified_by,
            modified_at=modified_at,
            favorite=favorite,
        )

        return extended_annotator


class StreamlitSherpaClient:
    register = {}

    def __init__(self, server: str, user: str, password: str, **kawargs):
        url = server[0:-1] if server.endswith('/') else server
        self.client = SherpaClient(base_url=f"{url}/api", verify_ssl=False, timeout=100)
        self.client.login_with_token(Credentials(email=user, password=password),
                                     project_access_mode=RequestJwtTokenProjectAccessMode.READ)
        StreamlitSherpaClient.register[self.token] = self

    @property
    def token(self):
        return self.client.token

    @staticmethod
    def from_token(token: str):
        return StreamlitSherpaClient.register.get(token, None)

    def clear_cache(self):
        self.get_projects.clear_cache()
        self.get_project_by_label.clear_cache()
        self.get_project_by_name.clear_cache()
        self.get_annotators.clear_cache()
        self.get_labels.clear_cache()
        self.get_annotator_by_label.clear_cache()
        self._get_plan.clear_cache()

    def cache_info(self):
        return {
            self.get_projects.__qualname__: self.get_projects.cache_info(),
            self.get_project_by_label.__qualname__: self.get_project_by_label.cache_info(),
            self.get_project_by_name.__qualname__: self.get_project_by_name.cache_info(),
            self.get_annotators.__qualname__: self.get_annotators.cache_info(),
            self.get_labels.__qualname__: self.get_labels.cache_info(),
            self.get_annotator_by_label.__qualname__: self.get_annotator_by_label.cache_info(),
            self._get_plan.__qualname__: self._get_plan.cache_info()
        }

    @lru_cache()
    def get_projects(self) -> List[ProjectBean]:
        r = get_projects.sync_detailed(client=self.client)
        if r.is_success:
            return r.parsed
        else:
            r.raise_for_status()

    @lru_cache()
    def get_project_by_label(self, label: str) -> ProjectBean:
        projects = self.get_projects()
        for p in projects:
            if p.label == label:
                return p
        return None

    @lru_cache()
    def get_project_by_name(self, name: str) -> ProjectBean:
        projects = self.get_projects()
        for p in projects:
            if p.name == name:
                return p
        return None

    @lru_cache()
    def get_sample_doc(self, project: Union[str, ProjectBean]) -> Document:
        pname = project.name if isinstance(project, ProjectBean) else project
        doc = None
        r = export_documents_sample.sync_detailed(pname, sample_size=1, client=self.client)
        if r.is_success:
            doc = r.parsed[0]
        else:
            r.raise_for_status()
        return doc

    @lru_cache()
    def get_annotators(self, project: Union[str, ProjectBean], annotator_types: Tuple[str] = None,
                       favorite_only: bool = False) -> List[ExtendedAnnotator]:
        pname = project.name if isinstance(project, ProjectBean) else project
        # st.write("get_annotators(", project, ", ", annotator_types,", ", favorite_only, ")")
        r = get_annotators_by_type.sync_detailed(pname, client=self.client)
        annotators: List[ExtendedAnnotator] = []
        if r.is_success:
            json_response: AnnotatorMultimap = r.parsed
            for type, ann_lst in json_response.additional_properties.items():
                for annotator in ann_lst:
                    if annotator_types is None or type in annotator_types:
                        if not favorite_only or annotator.favorite:
                            all_labels = {}
                            ann = annotator.to_dict()
                            ann['type'] = type
                            if type == 'plan':
                                plan: NamedAnnotationPlan = self._get_plan(pname, annotator.name)
                                if plan is not None:
                                    definition = plan.parameters
                                    for step in definition.pipeline:
                                        # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): step=", str(step))
                                        if isinstance(step, WithAnnotator) and step.project_name != project:
                                            step_labels = self.get_labels(step.project_name)
                                            all_labels.update(step_labels)
                                    ann.update(plan.to_dict())
                            project_labels = self.get_labels(pname)
                            all_labels.update(project_labels)
                            ext_ann: ExtendedAnnotator = ExtendedAnnotator.from_dict(ann)
                            ext_ann.labels = all_labels
                            annotators.append(ext_ann)
        else:
            r.raise_for_status()
        return annotators

    @lru_cache()
    def get_labels(self, project: Union[str, ProjectBean]) -> Dict[str, Label]:
        pname = project.name if isinstance(project, ProjectBean) else project
        r = get_labels.sync_detailed(pname, client=self.client)
        labels = {}
        if r.is_success:
            json_response = r.parsed
            for lab in json_response:
                labels[lab.name] = lab
        return labels

    @lru_cache()
    def get_annotator_by_label(self, project: Union[str, ProjectBean], label: str, annotator_types: Tuple[str] = None,
                               favorite_only: bool = False) -> ExtendedAnnotator:
        pname = project.name if isinstance(project, ProjectBean) else project
        annotators = self.get_annotators(pname, annotator_types, favorite_only)
        for ann in annotators:
            if ann.label == label:
                return ann
        return None

    @lru_cache()
    def _get_plan(self, project: Union[str, ProjectBean], name: str) -> NamedAnnotationPlan:
        pname = project.name if isinstance(project, ProjectBean) else project
        r = get_plan.sync_detailed(pname, name, client=self.client)
        if r.is_success:
            return r.parsed
        else:
            r.raise_for_status()

    def annotate_text(self, project: Union[str, ProjectBean], annotator: Union[str, ExtendedAnnotator],
                      text: str) -> AnnotatedDocument:
        pname = project.name if isinstance(project, ProjectBean) else project
        aname = annotator.name if isinstance(annotator, ExtendedAnnotator) else annotator
        long_client = self.client.with_timeout(1000)
        r = annotate_text_with.sync_detailed(pname, aname,
                                             text_body=text,
                                             client=long_client)
        # r = annotate_documents_with.sync_detailed(pname, aname,
        #                                           json_body=[InputDocument(text=text)],
        #                                           client=self.client)
        if r.is_success:
            doc = r.parsed
        else:
            r.raise_for_status()
        return doc

    @staticmethod
    def _file_from_response(r: Response):
        file: File = r.parsed
        file.mime_type = r.headers.get('Content-Type', 'application/octet-stream')
        if 'Content-Disposition' in r.headers:
            content_type, content_parameters = parse_options_header(r.headers['Content-Disposition'])
            # file.mime_type = content_type
            if b'filename' in content_parameters:
                file.file_name = content_parameters[b'filename'].decode("utf-8")
        return file

    def annotate_format_text(self, project: Union[str, ProjectBean], annotator: Union[str, ExtendedAnnotator],
                             text: str) -> File:
        pname = project.name if isinstance(project, ProjectBean) else project
        aname = annotator.name if isinstance(annotator, ExtendedAnnotator) else annotator
        long_client = self.client.with_timeout(1000)
        r = annotate_format_text_with_plan_ref.sync_detailed(pname, aname,
                                                             text_body=text,
                                                             client=long_client)
        # r = annotate_format_documents_with_plan_ref.sync_detailed(pname, aname,
        #                                                           json_body=[InputDocument(text=text)],
        #                                                           client=self.client)
        if r.is_success:
            return self._file_from_response(r)
        else:
            r.raise_for_status()

    def annotate_binary(self, project: Union[str, ProjectBean], annotator: Union[str, ExtendedAnnotator],
                        datafile: UploadedFile) -> List[AnnotatedDocument]:
        pname = project.name if isinstance(project, ProjectBean) else project
        aname = annotator.name if isinstance(annotator, ExtendedAnnotator) else annotator
        files = AnnotateFormatBinaryWithPlanRefMultipartData(
            file=File(file_name=datafile.name, payload=datafile.getvalue(), mime_type=datafile.type))
        long_client = self.client.with_timeout(1000)
        r = annotate_binary_with_plan_ref.sync_detailed(pname, aname,
                                                        multipart_data=files,
                                                        client=long_client)
        if r.is_success:
            docs = r.parsed
        else:
            r.raise_for_status()
        return docs

    def annotate_format_binary(self, project: Union[str, ProjectBean], annotator: Union[str, ExtendedAnnotator],
                               datafile: UploadedFile) -> File:
        pname = project.name if isinstance(project, ProjectBean) else project
        aname = annotator.name if isinstance(annotator, ExtendedAnnotator) else annotator
        files = AnnotateFormatBinaryWithPlanRefMultipartData(
            file=File(file_name=datafile.name, payload=datafile.getvalue(), mime_type=datafile.type))
        long_client = self.client.with_timeout(1000)
        r = annotate_format_binary_with_plan_ref.sync_detailed(pname, aname,
                                                               multipart_data=files,
                                                               client=long_client)
        if r.is_success:
            return self._file_from_response(r)
        else:
            r.raise_for_status()

    @staticmethod
    def documents_from_file(datafile: UploadedFile):
        jsondata = json.load(datafile)
        documents = jsondata if isinstance(jsondata, Sequence) else [jsondata]
        # for document in documents:
        #     for kd in list(document.keys()):
        #         if kd not in ["identifier", 'title', 'text', 'metadata', 'sentences', 'categories', 'annotations']:
        #             del document[kd]
        #         for sentence in document.get('sentences', []):
        #             for ks in list(sentence.keys()):
        #                 if ks not in ["start", 'end']:
        #                     del sentence[ks]
        #         for category in document.get('categories', []):
        #             for kc in list(category.keys()):
        #                 if kc not in ["identifier", 'labelName', 'score', "status", "createdDate",
        #                               "modifiedDate", "createdBy"]:
        #                     del category[kc]
        #         for ann in document.get('annotations', []):
        #             for ka in list(ann.keys()):
        #                 if ka not in ["start", 'end', "identifier", 'labelName', 'score', "text", "status",
        #                               "createdDate",
        #                               "modifiedDate", "createdBy"]:
        #                     del ann[ka]
        return documents

    def annotate_json(self, project: Union[str, ProjectBean], annotator: Union[str, ExtendedAnnotator],
                      datafile: UploadedFile) -> List[AnnotatedDocument]:
        pname = project.name if isinstance(project, ProjectBean) else project
        aname = annotator.name if isinstance(annotator, ExtendedAnnotator) else annotator
        documents = [InputDocument.from_dict(doc) for doc in self.documents_from_file(datafile)]
        long_client = self.client.with_timeout(1000)
        r = annotate_documents_with.sync_detailed(pname, aname,
                                                  json_body=documents,
                                                  client=long_client)
        if r.is_success:
            docs = r.parsed
        else:
            r.raise_for_status()
        return docs

    def annotate_format_json(self, project: Union[str, ProjectBean], annotator: Union[str, ExtendedAnnotator],
                             datafile: UploadedFile) -> File:
        pname = project.name if isinstance(project, ProjectBean) else project
        aname = annotator.name if isinstance(annotator, ExtendedAnnotator) else annotator
        documents = [InputDocument.from_dict(doc) for doc in self.documents_from_file(datafile)]
        long_client = self.client.with_timeout(1000)
        r = annotate_format_documents_with_plan_ref.sync_detailed(pname, aname,
                                                                  json_body=documents,
                                                                  client=long_client)
        if r.is_success:
            return self._file_from_response(r)
        else:
            r.raise_for_status()

# def main():
#     url_input = "https://sherpa-sandbox.kairntech.com/"
#     url = url_input[0:-1] if url_input.endswith('/') else url_input
#     client = StreamlitSherpaClient(url, "demo", "")
#     projects = client.get_projects()
#     print(projects)
#
#     for project in projects:
#         annotators = client.get_annotators(project.name)
#         print(annotators)
#         if annotators:
#             annotator = annotators[0]
#
#             ann = client.get_annotator_by_label(project.name, annotator.label)
#             print(ann)
#
#             doc = client.get_sample_doc(project.name)
#             print(doc)
#
#             labels = client.get_labels(project.name)
#             print(labels)
#
#             converter = ann.parameters.converter if ann.type == 'plan' else None
#             formatter = ann.parameters.formatter if ann.type == 'plan' else None
#             if converter and converter.name == 'tika':
#                 datafile = Path("/home/olivier/Téléchargements/attentats.odt")
#                 with datafile.open("rb") as fin:
#                     if formatter:
#                         result = client.annotate_format_binary(project.name, ann.name,
#                                                                UploadedFile(UploadedFileRec(id=1, name=datafile.name,
#                                                                                             type='application/octet-stream',
#                                                                                             data=fin.read())))
#                         print(result)
#
#                     else:
#                         result = client.annotate_binary(project.name, ann.name,
#                                                         UploadedFile(UploadedFileRec(id=1, name=datafile.name,
#                                                                                      type='application/octet-stream',
#                                                                                      data=fin.read())))
#                         print(result)
#
#             if formatter:
#                 result = client.annotate_format_text(project.name, ann.name, doc.text)
#                 print(result)
#
#             else:
#                 result = client.annotate_text(project.name, ann.name, doc.text)
#                 print(result)
#
#     pass
#
#
# import plac
#
# if __name__ == "__main__":
#     plac.call(main)
