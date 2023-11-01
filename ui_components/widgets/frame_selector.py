import streamlit as st
from ui_components.widgets.frame_movement_widgets import delete_frame, replace_image_widget,jump_to_single_frame_view_button
from ui_components.widgets.image_carousal import display_image
from ui_components.models import InternalFrameTimingObject, InternalShotObject
from utils.data_repo.data_repo import DataRepo
from ui_components.constants import WorkflowStageType
from utils import st_memory



def frame_selector_widget():
    data_repo = DataRepo()
    time1, time2 = st.columns([1,1])

    timing_list = data_repo.get_timing_list_from_shot(shot_uuid=st.session_state["shot_uuid"])
    shot = data_repo.get_shot_from_uuid(st.session_state["shot_uuid"])
    shot_list = data_repo.get_shot_list(shot.project.uuid)
    len_timing_list = len(timing_list) if len(timing_list) > 0 else 1.0
    st.progress(st.session_state['current_frame_index'] / len_timing_list)


    with time1:
        if 'prev_shot_index' not in st.session_state:
            st.session_state['prev_shot_index'] = shot.shot_idx

        # Get the list of shot names
        shot_names = [s.name for s in shot_list]

        # Add a selectbox for shot_name
        shot_name = st.selectbox('Shot Name', shot_names, key="current_shot_sidebar_selector")

        # Set current_shot_index based on the selected shot_name
        st.session_state['current_shot_index'] = shot_names.index(shot_name) + 1

        update_current_shot_index(st.session_state['current_shot_index'])
    if st.session_state['page'] == "Key Frames":
        with time2:
            if 'prev_frame_index' not in st.session_state:
                st.session_state['prev_frame_index'] = 1

            st.session_state['current_frame_index'] = st.number_input(f"Key frame # (out of {len(timing_list)})", 1, 
                                                                    len(timing_list), value=st.session_state['prev_frame_index'], 
                                                                    step=1, key="current_frame_sidebar_selector")
            
            update_current_frame_index(st.session_state['current_frame_index'])
        
        with st.expander(f"🖼️ Frame #{st.session_state['current_frame_index']} Details", expanded=True):
            if st_memory.toggle("Open", value=False, key="frame_toggle"):
                a1, a2 = st.columns([3,2])
                with a1:
                    st.success(f"Main Key Frame:")
                    display_image(st.session_state['current_frame_uuid'], stage=WorkflowStageType.STYLED.value, clickable=False)


                    # st.warning(f"Guidance Image:")
                    # display_image(st.session_state['current_frame_uuid'], stage=WorkflowStageType.SOURCE.value, clickable=False)
                with a2:
                    st.caption("Replace styled image")
                    replace_image_widget(st.session_state['current_frame_uuid'], stage=WorkflowStageType.STYLED.value)
                    
                st.info("In Context:")
                shot_list = data_repo.get_shot_list(shot.project.uuid)
                shot: InternalShotObject = data_repo.get_shot_from_uuid(st.session_state["shot_uuid"])

                # shot = data_repo.get_shot_from_uuid(st.session_state["shot_uuid"])
                timing_list: List[InternalFrameTimingObject] = shot.timing_list

                if timing_list and len(timing_list):
                    grid = st.columns(3)  # Change to 4 columns
                    for idx, timing in enumerate(timing_list):
                        with grid[idx % 3]:  # Change to 4 columns
                            if timing.primary_image and timing.primary_image.location:
                                st.image(timing.primary_image.location, use_column_width=True)
                            else:
                                st.warning("No primary image present")
                else:
                    st.warning("No keyframes present")

                st.markdown("---")

    else:
        shot_list = data_repo.get_shot_list(shot.project.uuid)
        shot: InternalShotObject = data_repo.get_shot_from_uuid(st.session_state["shot_uuid"])
        with st.expander(f"🎬 {shot.name} Details",expanded=True):
            if st_memory.toggle("Open", value=True, key="shot_details_toggle"):
                
                timing_list: List[InternalFrameTimingObject] = shot.timing_list

                if timing_list and len(timing_list):
                    grid = st.columns(3)  # Change to 3 columns
                    for idx, timing in enumerate(timing_list):
                        with grid[idx % 3]:  # Change to 3 columns
                            if timing.primary_image and timing.primary_image.location:
                                st.image(timing.primary_image.location, use_column_width=True)
                                
                                # Call jump_to_single_frame_view_button function
                                jump_to_single_frame_view_button(idx + 1, timing_list, f"jump_to_{idx + 1}")
                                    
                            else:
                                st.warning("No primary image present")
                else:
                    st.warning("No keyframes present")


def update_current_frame_index(index):
    data_repo = DataRepo()
    timing_list = data_repo.get_timing_list_from_shot(shot_uuid=st.session_state["shot_uuid"])

    st.session_state['current_frame_uuid'] = timing_list[index - 1].uuid
        
    if st.session_state['prev_frame_index'] != index:
        st.session_state['prev_frame_index'] = index
        st.session_state['current_frame_uuid'] = timing_list[index - 1].uuid
        st.session_state['reset_canvas'] = True
        st.session_state['frame_styling_view_type_index'] = 0
        st.session_state['frame_styling_view_type'] = "Individual View"
                                    
        st.rerun()


def update_current_shot_index(index):
    data_repo = DataRepo()
    shot_list = data_repo.get_shot_list(project_uuid=st.session_state["project_uuid"])

    st.session_state['shot_uuid'] = shot_list[index - 1].uuid
        
    if st.session_state['prev_shot_index'] != index:
        st.session_state['prev_shot_index'] = index
        st.session_state['shot_uuid'] = shot_list[index - 1].uuid
        st.session_state['reset_canvas'] = True
        st.session_state['frame_styling_view_type_index'] = 0
        st.session_state['frame_styling_view_type'] = "Individual View"
                                    
        st.rerun()       
