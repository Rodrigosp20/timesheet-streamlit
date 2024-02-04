import streamlit as st
import numpy as np

def team_tab():
    st.title("Profiles Definition")

    if st.button("Save Changes"):
        st.session_state.profile = np.copy(st.session_state.modified_profile)
    
    st.session_state.modified_profile = st.data_editor(
        st.session_state.profile, 
        num_rows="dynamic",
        use_container_width = True,
    )
        
    #print(st.session_state.profile)
    #print(st.session_state.modified_profile)

    st.title("Profiles and Persons Association")

    if st.button("Save Changes", key="save_profiles"):
        st.session_state.person = st.session_state.modified_person.copy()

    st.session_state.modified_person = st.data_editor(
        st.session_state.person, 
        num_rows="dynamic",
        column_config = {
            "Perfil": st.column_config.SelectboxColumn(
                "Profile",
                options = st.session_state.profile,
                required = True,
            ),
            "Nome": st.column_config.TextColumn(
                "Nome",
                width = "medium",
                required = True,
            ),
            "Genero": st.column_config.SelectboxColumn(
                "Genero",
                options = ["M", "F"],
                width="small",
                required = True,
            ),
            "Data Inicio": st.column_config.DateColumn(
                "Data Inicio",
                format="DD/MM/YYYY",
                step=1,
            ),
            "Data Rescisão": st.column_config.DateColumn(
                "Data Rescisão",
                format="DD/MM/YYYY",
                step=1,
            ),
        },
        use_container_width = True,
        hide_index=True
    )

    #print(st.session_state.modified_person)