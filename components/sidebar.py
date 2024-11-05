import streamlit as st
import pickle
import pandas as pd
from utils import *
from streamlit_option_menu import option_menu
from streamlit_antd_components import menu, MenuItem


def check_file_version(file):
    data = pickle.load(file)

    version = data.get('version', 1)
    if version < 2:

        data['persons'] = data['contracts'].drop_duplicates(subset="person")[['person', 'gender']]
        data['persons'].rename({'person':'name'}, axis='columns', inplace=True)

    if version < 3:
        data['inv_order_num'] = pd.DataFrame(columns=inv_order_num_schema.keys()).astype(inv_order_num_schema)

    return data

def read_file():
    """ Load file into cache memory """
    
    if file := st.session_state[f"file_{st.session_state.file_id}"]:
        data = check_file_version(file)

        st.session_state.activities= data['activities']
        st.session_state.persons= data['persons']
        st.session_state.contracts = data['contracts']
        st.session_state.projects = data['projects']
        st.session_state.sheets = data['sheets']
        st.session_state.planned_work = data['planned_work']
        st.session_state.real_work = data['real_work']
        st.session_state.working_days = data['working_days']
        st.session_state.inv_order_num = data['inv_order_num']
        st.session_state.company_name = file.name.split('.pkl')[0]
    else:
        st.session_state.activities = pd.DataFrame(columns=activities_schema.keys()).astype(activities_schema)
        st.session_state.persons = pd.DataFrame(columns=persons_schema.keys()).astype(persons_schema)
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)
        st.session_state.sheets = pd.DataFrame(columns=sheets_schema.keys()).astype(sheets_schema)
        st.session_state.planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)
        st.session_state.real_work = pd.DataFrame(columns=real_work_schema.keys()).astype(real_work_schema)
        st.session_state.working_days = pd.DataFrame(columns=working_days_schema.keys()).astype(working_days_schema)
        st.session_state.inv_order_num = pd.DataFrame(columns=inv_order_num_schema.keys()).astype(inv_order_num_schema)
        st.session_state.company_name = ""
    
    st.session_state.unsaved = False

def get_project_items() -> list:
    projects = [MenuItem(project_name, icon="diamond") for project_name in st.session_state.projects['name']]
    projects.insert(0,MenuItem("Adicionar Projeto", icon="folder-plus"))
    return projects

def sidebar_widget() -> str:
    st.markdown("""
    <style>
        div[data-testid="stSidebarContent"] div[data-testid="stFileUploader"] label {
            display: none;
        }
                
        div[data-testid='stVerticalBlock'] > div:nth-child(2) {
            background-color: rgb(14, 17, 23);
        }
                
                
        div[data-testid="stSidebarContent"] div[data-testid="stFileUploader"] section {
            border: 1px white dashed;
        }

        div[data-testid="stSidebarContent"] > div[data-testid="stVerticalBlockBorderWrapper"]:last-child {
            position: fixed;
            bottom: 15px;    
        }
                
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:

        st.session_state.company_name = st.text_input("Nome da Empresa", st.session_state.company_name)

        with st.container(border= True):
            st.header("Dados da empresa")

            st.file_uploader("Carrega o Ficheiro", type=".pkl", label_visibility='hidden', key=f"file_{st.session_state.file_id}", on_change=read_file)
            
            st.button("Guardar Ficheiro", use_container_width=True, on_click=save_data)
        
            if st.button("Descartar Dados", use_container_width=True):

                def reset_data():
                    create_session(reset=True)
            
                get_dialog(
                    "Descartar Dados", 
                    "Se continuar os dados da empresa serão descartados e perdidos se não tiverem sido guardada uma cópia do ficheiro", 
                    reset_data 
                )
            

        with st.container(border=True):
            
            selected_page = menu(
                items=[
                    MenuItem('Projetos', icon='kanban', children=get_project_items()),
                    MenuItem('Funcionários', icon='people-fill'),
                ], 
                open_all=True,
                index=1
            )  

        with st.container():

            with open("assets/MOD-16.3, Timesheets.pdf", "rb") as file:
                st.download_button(
                    label="Instrução de Trabalho",
                    data=file,
                    file_name="MOD-16.3, Timesheets.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with open("assets/Timesheet_Template.xlsx", "rb") as file:
                st.download_button(
                    label="Template Timesheet",
                    data=file,
                    file_name="Timesheet_Template.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )

    return selected_page