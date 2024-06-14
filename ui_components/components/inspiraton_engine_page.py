import time
from shared.constants import COMFY_BASE_PATH
import streamlit as st
import os
import requests
import shutil
from zipfile import ZipFile
from io import BytesIO
from ui_components.constants import CreativeProcessType
from ui_components.methods.video_methods import upscale_video
from ui_components.widgets.inspiration_engine import inspiration_engine_element
from ui_components.widgets.timeline_view import timeline_view
from ui_components.components.explorer_page import gallery_image_view
from utils import st_memory
from utils.data_repo.data_repo import DataRepo

from ui_components.widgets.sidebar_logger import sidebar_logger
from ui_components.components.explorer_page import generate_images_element


def inspiration_engine_page(shot_uuid: str, h2):
    data_repo = DataRepo()
    shot = data_repo.get_shot_from_uuid(shot_uuid)
    if not shot:
        st.error("Shot not found")
    else:
        project_uuid = shot.project.uuid
        project = data_repo.get_project_from_uuid(project_uuid)

        with st.sidebar:
            views = CreativeProcessType.value_list()

            if "view" not in st.session_state:
                st.session_state["view"] = views[0]

            st.write("")

            with st.expander("🔍 Generation log", expanded=True):
                # if st_memory.toggle("Open", value=True, key="generaton_log_toggle"):
                sidebar_logger(st.session_state["shot_uuid"])

            st.write("")
            with st.expander("🪄 Timeline", expanded=True):
                timeline_view(shot_uuid, "🪄 Timeline", view="sidebar")

            


        st.markdown(f"#### :green[{st.session_state['main_view_type']}] > :red[{st.session_state['page']}]")
        st.markdown("***")

        st.markdown("### ✨ Generate images")
        st.write("##### _\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_")

        inspiration_engine_element(
            position="explorer", project_uuid=project_uuid, timing_uuid=None, shot_uuid=None
        )

        st.markdown("***")
        gallery_image_view(
            project_uuid,
            False,
            view=[
                "add_and_remove_from_shortlist",
                "view_inference_details",
                "shot_chooser",
                "add_to_any_shot",
            ],
        )
     