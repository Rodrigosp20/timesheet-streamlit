import streamlit as st
import pickle
import pandas as pd
from utils import *
from streamlit_modal import Modal

def read_file():
    """ Load file into cache memory """
    
    if file := st.session_state[f"file_{st.session_state.file_id}"]:
        data = pickle.load(file)
        st.session_state.activities= data['activities']
        st.session_state.contracts = data['contracts']
        st.session_state.projects = data['projects']
        st.session_state.sheets = data['sheets']
        st.session_state.planned_work = data['planned_work']
        st.session_state.real_work = data['real_work']
        st.session_state.working_days = data['working_days']
        st.session_state.company_name = file.name.split('.pkl')[0]
    else:
        st.session_state.activities = pd.DataFrame(columns=activities_schema.keys()).astype(activities_schema)
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)
        st.session_state.sheets = pd.DataFrame(columns=sheets_schema.keys()).astype(sheets_schema)
        st.session_state.planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)
        st.session_state.real_work = pd.DataFrame(columns=real_work_schema.keys()).astype(real_work_schema)
        st.session_state.working_days = pd.DataFrame(columns=working_days_schema.keys()).astype(working_days_schema)
        st.session_state.company_name = ""

def sidebar_widget() -> str:

    with st.sidebar:

        st.title("Ficheiro de Dados")

        st.file_uploader("Carrega o Ficheiro", type=".pkl", label_visibility='hidden', key=f"file_{st.session_state.file_id}", on_change=read_file)
        
        st.button("Guardar Progresso", use_container_width=True, on_click=save_data)
       
        modal = Modal("Descartar todas as alterações ", key="delete_data_modal")
        
        if st.button("Descartar Todas Alterações", use_container_width=True):
            modal.open()

        if modal.is_open():
            with modal.container():
                st.write('<p style="text-align: center; margin-bottom:40px;">Irá perder trabalho não guardado, continuar mesmo assim ?</p>', unsafe_allow_html=True)                

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Eliminar", use_container_width=True):
                        create_session(reset=True)
                        modal.close()
                        st.rerun()

                with col2:
                    if st.button("Cancelar", use_container_width=True):
                        modal.close()
        
        st.divider()

        st.session_state.company_name = st.text_input("Empresa", st.session_state.company_name)

        return st.selectbox('Projeto', options = [""] + st.session_state.projects['name'].to_list(), placeholder="Escolhe um projeto", on_change=reset_key)