import streamlit as st
import pickle
import pandas as pd
from utils import *

def read_file():
    """ Load file into cache memory """
    
    if file := st.session_state.file:
        data = pickle.load(file)
        st.session_state.activities= data['activities']
        st.session_state.contracts = data['contracts']
        st.session_state.projects = data['projects']
        st.session_state.sheets = data['sheets']
        st.session_state.planned_work = data['planned_work']
        st.session_state.real_work = data['real_work']
    else:
        st.session_state.activities = pd.DataFrame(columns=activities_schema.keys()).astype(activities_schema)
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)
        st.session_state.sheets = pd.DataFrame(columns=sheets_schema.keys()).astype(sheets_schema)
        st.session_state.planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)
        st.session_state.real_work = pd.DataFrame(columns=real_work_schema.keys()).astype(real_work_schema)


def sidebar_widget() -> str:

    with st.sidebar:

        st.title("Ficheiro de Dados")

        st.file_uploader("Carrega o Ficheiro", type=".pkl", label_visibility='hidden', key="file", on_change=read_file)

        st.button("Guardar Progresso", use_container_width=True, on_click=save_data)

        st.divider()

        return st.selectbox('Seleciona um Projeto', options = [""] + st.session_state.projects['name'].to_list(), placeholder="Escolhe um projeto", on_change=reset_key)