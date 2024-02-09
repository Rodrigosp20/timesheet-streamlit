import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import datetime, tempfile, os, base64, pickle
from utils import *
from team import team_tab
from timeline import timeline_tab
from io import BytesIO


projects_schema = {
    "name": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
    "man_sheet": "object",
    "planned_work": "object"
}

man_sheet_schema = {
    "person" : "string",
    "indicator" : "string",
}

planned_work_schema = {
    "person" : "string",
    "wp" : "string",
    "activity" : "string",
}

persons_schema = {
    "person": "string",
    "nif": "string"
}

timelines_schema = {
    "project": "string",
    "wp": "string",
    "activity": "string",
    "trl": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
}

contracts_schema = {
    "project":"string",
    "person":"string",
    "nif":"string",
    "profile":"string",
    "gender": "string",
    "value": "float64",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
}

def recalculate_horas_trabalhadas(df):
    df_calcs = pd.DataFrame(columns=df.columns, index=['Horas trabalhadas', 'FTE'])

    df_calcs.loc['Horas trabalhadas'] = df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Faltas'] - df.loc['Férias']
    df_calcs.loc['FTE'] = df.loc['Horas reais'] / (df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Férias'])

    return df_calcs

def update_sheets():
    for person in st.session_state.project['persons'].itertuples(index=False):

        if person.Nome not in st.session_state.project['sheets'].values():

            person_sheets = {}
            
            start_date = st.session_state.project['start_date']
            end_date = st.session_state.project['end_date']

            months_range = pd.date_range(start=start_date, end=end_date, freq='MS')
            formatted_columns = [month.strftime('%b/%y') for month in months_range]

            df = pd.DataFrame(columns=formatted_columns, index=['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas reais', 'Horas trabalhadas', 'FTE'])
            
            df.loc['Jornada Diária'] = 8
            df.loc['Dias Úteis'] = 20
            df.loc['Faltas'] = 0
            df.loc['Férias'] = 0
            df.loc['Horas reais'] = 0
            
            df.loc['Horas trabalhadas'] = df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Faltas'] - df.loc['Férias']
            df.loc['FTE'] = df.loc['Horas reais'] / (df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Férias'])

            person_sheets['sheet'] = df

            for wp, activites in st.session_state.project['timeline'].items():

                df = pd.DataFrame(columns=['TRL']+formatted_columns, index=activites.keys())
                for act in activites.keys():
                    df.loc[act,'TRL'] = st.session_state.project['timeline'][wp][act]['trl']

                df.loc[:, df.columns != 'TRL'] = 0

                person_sheets[wp] = df
        
        else:
            pass
            #TODO: Modify Dataframe

        st.session_state.project['sheets'][person.Nome] = person_sheets

def generate_excel_content():

    with open('data.pkl', 'wb') as f:
        pickle.dump({
            'timelines':st.session_state.timelines,
            'contracts':st.session_state.contracts,
            'projects':st.session_state.projects,
            'persons':st.session_state.persons
        }, f)

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        st.session_state.timelines.to_excel(writer, sheet_name='Timelines', index=False)
        st.session_state.persons.to_excel(writer, sheet_name='Persons', index=False)
        st.session_state.contracts.to_excel(writer, sheet_name='Contracts', index=False)
        st.session_state.projects.to_excel(writer, sheet_name='Projects', index=False)

    excel_buffer.seek(0)
    return excel_buffer.read()

@st.cache_resource
def load_file(file):
    #dfs = pd.read_excel(file, sheet_name=None)
    dfs = pickle.load(file)
    st.session_state.timelines= dfs['timelines']
    st.session_state.persons = dfs['persons']
    st.session_state.contracts = dfs['contracts']
    st.session_state.projects = dfs['projects']


def load_empty_state():

    if 'timelines' not in st.session_state:
        st.session_state.timelines = pd.DataFrame(columns=timelines_schema.keys()).astype(timelines_schema)
    
    if 'persons' not in st.session_state:
        st.session_state.persons = pd.DataFrame(columns=persons_schema.keys()).astype(persons_schema)
    
    if 'contracts' not in st.session_state:
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
    
    if 'projects' not in st.session_state:
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)

    if 'project' not in st.session_state:
        st.session_state.project = pd.DataFrame()
        st.session_state.project_name = None

    if 'key' not in st.session_state:
        st.session_state.key = 0

def main():
  
    load_empty_state()
    
    ## SIDEBAR WIDGETS

    st.sidebar.title("Ficheiro de Dados")
    if file:= st.sidebar.file_uploader("Carrega o Ficheiro", type=".pkl", label_visibility='hidden'):
        load_file(file)

    if st.sidebar.button("Save Progress", use_container_width=True):
        excel_content = generate_excel_content()
        b64 = base64.b64encode(excel_content).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="output.xlsx">Download Excel File</a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)

    st.sidebar.divider()

    selected_project = st.sidebar.selectbox('Select a Project', options = [None] + st.session_state.projects['name'].to_list())

    if selected_project != st.session_state.project_name:
        st.session_state.project_name = selected_project
        if selected_project != None:
            st.session_state.project = st.session_state.projects[st.session_state.projects == selected_project].iloc[0]
        else:
            st.session_state.project = pd.DataFrame()

        st.rerun()

    #####################
    
    if st.session_state.project.empty:

        projects = st.session_state.projects
        st.title("Criar Projeto")

        project_name = st.text_input("Nome do projeto")
        start_date = st.date_input("Data de inicio", format="DD/MM/YYYY")
        end_date = st.date_input("Data de encerramento", format="DD/MM/YYYY")

        if st.button("Criar Projeto"):
            if project_name and start_date and end_date:

                #if projects

                if start_date < end_date:
                    ind = projects.index.max() + 1
                    
                    for month in  date_range(start_date, end_date):
                        man_sheet_schema[month] = 'float64'
                        planned_work_schema[month] = 'float64'
                    
                    man_sheet = pd.DataFrame(columns=man_sheet_schema.keys()).astype(man_sheet_schema)
                    planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)

                    projects.loc[ind] = [project_name, start_date, end_date, man_sheet, planned_work]

                    st.rerun()
        
        return


    tab_project, tab_timeline, tab_team, tab_sheet, tab_imputations = st.tabs(["Projeto", "Cronograma", "Equipa", "Pessoal", "Imputação"])

    with tab_project:
        st.title(f"{st.session_state.project_name}")

        project = st.session_state.project

        start_date = st.date_input("Data Inicio", value=project.loc['start_date'], format="DD/MM/YYYY")
        end_date = st.date_input("Data Fim", value=project.loc['end_date'], format="DD/MM/YYYY")

        if st.button("Save changes"):
            # Logistic of change Project Date
            st.rerun()
    
    with tab_timeline:
        name = st.session_state.project_name
        timelines = st.session_state.timelines

        timeline = timelines[timelines['project'] == name]

        timeline_mod = st.data_editor(
            timeline.iloc[:, 1:],
            column_config={
                "wp": st.column_config.SelectboxColumn(
                    "WP",
                    required=True
                ),
                "trl": st.column_config.SelectboxColumn(
                    "TRL",
                    options=['TRL 3-4', 'TRL 5-9'],
                    required=True
                ),
                "start_date": st.column_config.DateColumn(
                    "Data de Inicio",
                    min_value=st.session_state.project["start_date"],
                    default=st.session_state.project["start_date"],
                    format="DD/MM/YYYY",
                    required=True
                ),
                "end_date": st.column_config.DateColumn(
                    "Data de Termino",
                    min_value=st.session_state.project["end_date"],
                    default=st.session_state.project["end_date"],
                    format="DD/MM/YYYY",
                    required=True
                )
            },
            hide_index=True,
            num_rows='dynamic',
            use_container_width=True
        )

        if st.button("Save Changes"):
            #Logistic of change activities
            st.rerun()
        
    
    with tab3:
        name = st.session_state.project_name
        contracts = st.session_state.contracts

        contracts = contracts[contracts['project'] == name]

        contacts_mod = st.data_editor(
                contracts.iloc[:, 1:], 
                num_rows="dynamic",
                column_config = {
                    "person": st.column_config.TextColumn(
                        "Nome",
                        width = "medium",
                        required = True,
                    ),
                    "nif": st.column_config.TextColumn(
                        "NIF",
                        width = "medium",
                        required = True,
                    ),
                    "profile": st.column_config.TextColumn(
                        "Perfil",
                        width="medium",
                        required = True,
                    ),
                    "gender": st.column_config.SelectboxColumn(
                        "Genero",
                        options = ["M", "F"],
                        width="small",
                        required = True,
                    ),
                    "value": st.column_config.NumberColumn(
                        "Montante",
                        required=True
                    ),
                    "start_date": st.column_config.DateColumn(
                        "Data de Inicio",
                        format="DD/MM/YYYY",
                        default=st.session_state.project['start_date'],
                        step=1,
                    ),
                    "end_date": st.column_config.DateColumn(
                        "Data de Termino",
                        format="DD/MM/YYYY",
                        default=st.session_state.project['end_date'],
                        step=1,
                    ),
                },
                use_container_width = True,
                hide_index=True
            )

        if st.button("Save Changes"):
            #Logistic of change team
            st.rerun()

    with tab5:

        man_sheet = st.session_state.project["man_sheet"]

        contracts = st.session_state.contracts

        if person := st.selectbox("Pessoa", options= st.session_state.project['sheets'].keys()):

            modifications = st.data_editor(
                st.session_state.project['sheets'][person]['sheet'].iloc[0:5],
                key = f"{person}_sheet",
                use_container_width=True
            )



        
        
    
if __name__ == "__main__":
    main()
