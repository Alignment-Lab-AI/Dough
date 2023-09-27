
import os
import time
from io import BytesIO
from typing import List
import requests as r
from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from ui_components.constants import WorkflowStageType
from utils.data_repo.data_repo import DataRepo

from utils import st_memory
from utils.data_repo.data_repo import DataRepo
from utils import st_memory
from ui_components.methods.common_methods import execute_image_edit
from ui_components.models import InternalFrameTimingObject, InternalSettingObject
from streamlit_image_comparison import image_comparison


def inpainting_element(timing_uuid):

    which_stage_to_inpaint = st_memory.radio("Which stage to work on?", ["Styled Key Frame", "Unedited Key Frame"], horizontal=True, key="which_stage_inpainting")
    
    if which_stage_to_inpaint == "Styled Key Frame":
        stage = WorkflowStageType.STYLED.value
    elif which_stage_to_inpaint == "Unedited Key Frame":
        stage = WorkflowStageType.SOURCE.value
    data_repo = DataRepo()
    timing = data_repo.get_timing_from_uuid(timing_uuid)
    timing_details: List[InternalFrameTimingObject] = data_repo.get_timing_list_from_project(
        timing.project.uuid)
    project_settings: InternalSettingObject = data_repo.get_project_setting(
        timing.project.uuid)

    if len(timing_details) == 0:
        st.info("You need to add  key frames first in the Key Frame Selection section.")
    else:
        main_col_1, main_col_2 = st.columns([1, 2])

        with main_col_1:
            st.write("")

        # initiative value
        if "current_frame_uuid" not in st.session_state:
            st.session_state['current_frame_uuid'] = timing_details[0].uuid


        if "edited_image" not in st.session_state:
            st.session_state.edited_image = ""

        if stage == WorkflowStageType.STYLED.value and len(timing.alternative_images_list) == 0:
            st.info("You need to add a style first in the Style Selection section.")
        else:
            if stage == WorkflowStageType.SOURCE.value:
                editing_image = timing.source_image.location
            elif stage == WorkflowStageType.STYLED.value:
                variants = timing.alternative_images_list
                editing_image = timing.primary_image_location

            width = int(project_settings.width)
            height = int(project_settings.height)

            if editing_image == "":
                st.error(
                    f"You don't have a {stage} image yet so you can't edit it.")
            else:
                with main_col_1:
                    if 'index_of_type_of_mask_selection' not in st.session_state:
                        st.session_state['index_of_type_of_mask_selection'] = 0
                    mask_selection_options = ["Manual Background Selection", "Automated Background Selection",
                                              "Automated Layer Selection", "Re-Use Previous Mask", "Invert Previous Mask"]
                    type_of_mask_selection = st.radio("How would you like to select what to edit?", mask_selection_options,
                                                      horizontal=True, index=st.session_state['index_of_type_of_mask_selection'])
                    if st.session_state['index_of_type_of_mask_selection'] != mask_selection_options.index(type_of_mask_selection):
                        st.session_state['index_of_type_of_mask_selection'] = mask_selection_options.index(
                            type_of_mask_selection)
                        st.experimental_rerun()

                    if "which_layer" not in st.session_state:
                        st.session_state['which_layer'] = "Background"
                        st.session_state['which_layer_index'] = 0

                    if type_of_mask_selection == "Automated Layer Selection":
                        layers = ["Background", "Middleground", "Foreground"]
                        st.session_state['which_layer'] = st.multiselect(
                            "Which layers would you like to replace?", layers)

                if type_of_mask_selection == "Manual Background Selection":
                    if st.session_state['edited_image'] == "":
                        with main_col_1:
                            if editing_image.startswith("http"):
                                canvas_image = r.get(editing_image)
                                canvas_image = Image.open(
                                    BytesIO(canvas_image.content))
                            else:
                                canvas_image = Image.open(editing_image)
                            if 'drawing_input' not in st.session_state:
                                st.session_state['drawing_input'] = 'Magic shapes 🪄'
                            col1, col2 = st.columns([6, 3])

                            with col1:
                                st.session_state['drawing_input'] = st.radio(
                                    "Drawing tool:",
                                    ("Make shapes 🪄", "Move shapes 🏋🏾‍♂️", "Make squares □", "Draw lines ✏️"), horizontal=True,
                                )

                            if st.session_state['drawing_input'] == "Move shapes 🏋🏾‍♂️":
                                drawing_mode = "transform"
                                st.info(
                                    "To delete something, just move it outside of the image! 🥴")
                            elif st.session_state['drawing_input'] == "Make shapes 🪄":
                                drawing_mode = "polygon"
                                st.info("To end a shape, right click!")
                            elif st.session_state['drawing_input'] == "Draw lines ✏️":
                                drawing_mode = "freedraw"
                                st.info("To draw, draw! ")
                            elif st.session_state['drawing_input'] == "Make squares □":
                                drawing_mode = "rect"

                            with col2:
                                if drawing_mode == "freedraw":
                                    stroke_width = st.slider(
                                        "Stroke width: ", 1, 25, 12)
                                else:
                                    stroke_width = 3

                        with main_col_2:

                            realtime_update = True

                            canvas_result = st_canvas(
                                fill_color="rgba(0, 0, 0)",
                                stroke_width=stroke_width,
                                stroke_color="rgba(0, 0, 0)",
                                background_color="rgb(255, 255, 255)",
                                background_image=canvas_image,
                                update_streamlit=realtime_update,
                                height=height,
                                width=width,
                                drawing_mode=drawing_mode,
                                display_toolbar=True,
                                key="full_app",
                            )

                            if 'image_created' not in st.session_state:
                                st.session_state['image_created'] = 'no'

                            if canvas_result.image_data is not None:
                                img_data = canvas_result.image_data
                                im = Image.fromarray(
                                    img_data.astype("uint8"), mode="RGBA")
                                create_or_update_mask(
                                    st.session_state['current_frame_uuid'], im)
                    else:
                        image_file = data_repo.get_file_from_uuid(st.session_state['edited_image'])
                        image_comparison(
                            img1=editing_image,
                            img2=image_file.location, starting_position=5, label1="Original", label2="Edited")
                        if st.button("Reset Canvas"):
                            st.session_state['edited_image'] = ""
                            st.experimental_rerun()

                elif type_of_mask_selection == "Automated Background Selection" or type_of_mask_selection == "Automated Layer Selection" or type_of_mask_selection == "Re-Use Previous Mask" or type_of_mask_selection == "Invert Previous Mask":
                    with main_col_1:
                        if type_of_mask_selection in ["Re-Use Previous Mask", "Invert Previous Mask"]:
                            if not timing_details[st.session_state['current_frame_index'] - 1].mask:
                                st.info(
                                    "You don't have a previous mask to re-use.")
                            else:
                                mask1, mask2 = st.columns([2, 1])
                                with mask1:
                                    if type_of_mask_selection == "Re-Use Previous Mask":
                                        st.info(
                                            "This will update the **black pixels** in the mask with the pixels from the image you are editing.")
                                    elif type_of_mask_selection == "Invert Previous Mask":
                                        st.info(
                                            "This will update the **white pixels** in the mask with the pixels from the image you are editing.")
                                    st.image(
                                        timing_details[st.session_state['current_frame_index'] - 1].mask.location, use_column_width=True)

                    with main_col_2:
                        if st.session_state['edited_image'] == "":
                            st.image(editing_image, use_column_width=True)
                        else:
                            image_file = data_repo.get_file_from_uuid(st.session_state['edited_image'])
                            image_comparison(
                                img1=editing_image,
                                img2=image_file.location, starting_position=5, label1="Original", label2="Edited")
                            if st.button("Reset Canvas"):
                                st.session_state['edited_image'] = ""
                                st.experimental_rerun()

                with main_col_1:

                    if "type_of_mask_replacement" not in st.session_state:
                        st.session_state["type_of_mask_replacement"] = "Replace With Image"
                        st.session_state["index_of_type_of_mask_replacement"] = 0

                    types_of_mask_replacement = [
                        "Inpainting", "Replace With Image"]
                    st.session_state["type_of_mask_replacement"] = st.radio(
                        "Select type of edit", types_of_mask_replacement, horizontal=True, index=st.session_state["index_of_type_of_mask_replacement"])

                    if st.session_state["index_of_type_of_mask_replacement"] != types_of_mask_replacement.index(st.session_state["type_of_mask_replacement"]):
                        st.session_state["index_of_type_of_mask_replacement"] = types_of_mask_replacement.index(
                            st.session_state["type_of_mask_replacement"])
                        st.experimental_rerun()

                    if st.session_state["type_of_mask_replacement"] == "Replace With Image":
                        prompt = ""
                        negative_prompt = ""
                        background_list = [f for f in os.listdir(
                            f'videos/{timing.project.uuid}/assets/resources/backgrounds') if f.endswith('.png')]
                        background_list = [f for f in os.listdir(
                            f'videos/{timing.project.uuid}/assets/resources/backgrounds') if f.endswith('.png')]
                        sources_of_images = ["Uploaded", "From Other Frame"]
                        if 'index_of_source_of_image' not in st.session_state:
                            st.session_state['index_of_source_of_image'] = 0
                        source_of_image = st.radio("Select type of image", sources_of_images,
                                                   horizontal=True, index=st.session_state['index_of_source_of_image'])

                        if st.session_state['index_of_source_of_image'] != sources_of_images.index(source_of_image):
                            st.session_state['index_of_source_of_image'] = sources_of_images.index(
                                source_of_image)
                            st.experimental_rerun()

                        if source_of_image == "Uploaded":
                            btn1, btn2 = st.columns([1, 1])
                            with btn1:
                                uploaded_files = st.file_uploader(
                                    "Add more background images here", accept_multiple_files=True)
                                if st.button("Upload Backgrounds"):
                                    for uploaded_file in uploaded_files:
                                        with open(os.path.join(f"videos/{timing.project.uuid}/assets/resources/backgrounds", uploaded_file.name), "wb") as f:
                                            f.write(uploaded_file.getbuffer())
                                            st.success(
                                                "Your backgrounds are uploaded file - they should appear in the dropdown.")
                                            background_list.append(
                                                uploaded_file.name)
                                            time.sleep(1.5)
                                            st.experimental_rerun()
                            with btn2:
                                background_selection = st.selectbox(
                                    "Range background", background_list)
                                background_image = f'videos/{timing.project.uuid}/assets/resources/backgrounds/{background_selection}'
                                if background_list != []:
                                    st.image(f"{background_image}",
                                             use_column_width=True)
                        elif source_of_image == "From Other Frame":
                            btn1, btn2 = st.columns([1, 1])
                            with btn1:
                                which_stage_to_use = st.radio(
                                    "Select stage to use:", WorkflowStageType.value_list())
                                which_image_to_use = st.number_input(
                                    "Select image to use:", min_value=0, max_value=len(timing_details)-1, value=0)
                                if which_stage_to_use == WorkflowStageType.SOURCE.value:
                                    background_image = timing_details[which_image_to_use].source_image.location

                                elif which_stage_to_use == WorkflowStageType.STYLED.value:
                                    background_image = timing_details[which_image_to_use].primary_image_location
                            with btn2:
                                st.image(background_image,
                                         use_column_width=True)

                    elif st.session_state["type_of_mask_replacement"] == "Inpainting":
                        btn1, btn2 = st.columns([1, 1])
                        with btn1:
                            prompt = st.text_area("Prompt:", help="Describe the whole image, but focus on the details you want changed!",
                                                  value=project_settings.default_prompt)
                        with btn2:
                            negative_prompt = st.text_area(
                                "Negative Prompt:", help="Enter any things you want to make the model avoid!", value=project_settings.default_negative_prompt)

                    edit1, edit2 = st.columns(2)

                    with edit1:
                        if st.button(f'Run Edit On Current Image'):
                            if st.session_state["type_of_mask_replacement"] == "Inpainting":
                                edited_image = execute_image_edit(type_of_mask_selection, st.session_state["type_of_mask_replacement"],
                                                                  "", editing_image, prompt, negative_prompt, width, height, st.session_state['which_layer'], st.session_state['current_frame_uuid'])
                                st.session_state['edited_image'] = edited_image.uuid
                            elif st.session_state["type_of_mask_replacement"] == "Replace With Image":
                                edited_image = execute_image_edit(type_of_mask_selection, st.session_state["type_of_mask_replacement"],
                                                                  background_image, editing_image, "", "", width, height, st.session_state['which_layer'], st.session_state['current_frame_uuid'])
                                st.session_state['edited_image'] = edited_image.uuid
                            st.experimental_rerun()

                    with edit2:
                        if st.session_state['edited_image'] != "":
                            if st.button("Promote Last Edit", type="primary"):
                                if stage == WorkflowStageType.SOURCE.value:
                                    data_repo.update_specific_timing(
                                        st.session_state['current_frame_uuid'], source_image_id=st.session_state['edited_image'])
                                elif stage == WorkflowStageType.STYLED.value:
                                    number_of_image_variants = add_image_variant(
                                        st.session_state['edited_image'], st.session_state['current_frame_uuid'])
                                    promote_image_variant(
                                        st.session_state['current_frame_uuid'], number_of_image_variants - 1)
                                st.session_state['edited_image'] = ""
                                st.experimental_rerun()
                        else:
                            if st.button("Run Edit & Promote"):
                                if st.session_state["type_of_mask_replacement"] == "Inpainting":
                                    edited_image = execute_image_edit(type_of_mask_selection, st.session_state["type_of_mask_replacement"],
                                                                      "", editing_image, prompt, negative_prompt, width, height, st.session_state['which_layer'], st.session_state['current_frame_uuid'])
                                    st.session_state['edited_image'] = edited_image.uuid
                                elif st.session_state["type_of_mask_replacement"] == "Replace With Image":
                                    edited_image = execute_image_edit(type_of_mask_selection, st.session_state["type_of_mask_replacement"],
                                                                      background_image, editing_image, "", "", width, height, st.session_state['which_layer'], st.session_state['current_frame_uuid'])
                                    st.session_state['edited_image'] = edited_image.uuid

                                if stage == WorkflowStageType.SOURCE.value:
                                    data_repo.update_specific_timing(
                                        st.session_state['current_frame_uuid'], source_image_id=st.session_state['edited_image'])
                                elif stage == WorkflowStageType.STYLED.value:
                                    number_of_image_variants = add_image_variant(
                                        edited_image.uuid, st.session_state['current_frame_uuid'])
                                    promote_image_variant(
                                        st.session_state['current_frame_uuid'], number_of_image_variants - 1)

                                st.session_state['edited_image'] = ""
                                st.success("Image promoted!")
                                st.experimental_rerun()