from sherpa_streamlit import visualize

default_text = """This is a simple sample text
"""
visualize(default_text,
          favorite_only=True,
          sidebar_title="KAIRNTECH Sherpa",
          sidebar_description="Customizable Sherpa demonstration")
