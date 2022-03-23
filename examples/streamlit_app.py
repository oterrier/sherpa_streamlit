from sherpa_streamlit import visualize

default_text = """This is a simple sample text
"""
visualize(
    default_text,
    show_json=True,
    sidebar_title="KAIRNTECH Sherpa",
    sidebar_description="Customizable Sherpa demonstration",
    page_title="KAIRNTECH Sherpa demonstration page",
    page_description="""This service allows to submit a text fragment and vizualize the resulting annotations""",
)
