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
    "planned_work": "object",
    "time_allocation": "object",
    "cost_allocation": "object"
}

man_sheet_schema = {
    "person" : "string",
    "indicator" : "string",
}

planned_work_schema = {
    "person" : "string",
    "wp" : "string",
    "activity" : "string",
    "trl": "string"
}

time_allocation_schema = {
    "person" : "string",
    "wp" : "string",
    "activity" : "string",
    "trl": "string"
}

cost_allocation_schema = {
    "person" : "string",
    "wp" : "string",
    "activity" : "string",
    "trl": "string"
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


def save_data():
    with open('data.pkl', 'wb') as f:
        pickle.dump({
            'timelines':st.session_state.timelines,
            'contracts':st.session_state.contracts,
            'projects':st.session_state.projects,
            'persons':st.session_state.persons
        }, f)

def load_file(file):
    if file:
        dfs = pickle.load(file)
        st.session_state.timelines= dfs['timelines']
        st.session_state.persons = dfs['persons']
        st.session_state.contracts = dfs['contracts']
        st.session_state.projects = dfs['projects']
    else:
        st.session_state.timelines = pd.DataFrame(columns=timelines_schema.keys()).astype(timelines_schema)
        st.session_state.persons = pd.DataFrame(columns=persons_schema.keys()).astype(persons_schema)
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)

def load_empty_state():

    if 'project' not in st.session_state:
        st.session_state.project = pd.DataFrame()
        st.session_state.project_name = None

    if 'key' not in st.session_state:
        st.session_state.key = 0

def value_changed(label, value):

    if label not in st.session_state:
        st.session_state[label] = value
        return True

    if st.session_state[label] != value:
        st.session_state[label] = value
        return True
    
    st.session_state[label] = value
    return False


def main():
  
    load_empty_state()
    
    ## SIDEBAR WIDGETS

    st.sidebar.title("Ficheiro de Dados")
    file = st.sidebar.file_uploader("Carrega o Ficheiro", type=".pkl", label_visibility='hidden')
    if value_changed("selected_file", file):

        load_file(file)

    if st.sidebar.button("Save Progress", use_container_width=True):
        save_data()

    st.sidebar.divider()

    selected_project = st.sidebar.selectbox('Select a Project', options = [None] + st.session_state.projects['name'].to_list())
    
    if value_changed("project_name", selected_project):
        
        if selected_project != None:
            st.session_state.project = st.session_state.projects[st.session_state.projects['name'] == selected_project].iloc[0]
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

                if projects[projects['name'] == project_name].empty and start_date < end_date:
                  
                    for month in  date_range(start_date, end_date):
                        man_sheet_schema[month] = 'float64'
                        planned_work_schema[month] = 'float64'
                        cost_allocation_schema[month] = 'float64'
                        time_allocation_schema[month] = 'float64'
                    
                    man_sheet = pd.DataFrame(columns=man_sheet_schema.keys()).astype(man_sheet_schema)
                    planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)
                    cost_allocation = pd.DataFrame(columns=cost_allocation_schema.keys()).astype(cost_allocation_schema)
                    time_allocation = pd.DataFrame(columns=time_allocation_schema.keys()).astype(time_allocation_schema)
                
                    projects.loc[len(projects)] = [project_name, start_date, end_date, man_sheet, planned_work, cost_allocation, time_allocation]

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
                "wp": st.column_config.TextColumn(
                    "WP",
                    required=True
                ),
                "activity": st.column_config.TextColumn(
                    "Atividade",
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
            if len(timeline_mod["activity"]) != len(set(timeline_mod["activity"])):
                st.toast("Duplicate values found in the 'Names' column! Please ensure all values are unique.")

            timeline_mod.insert(0,"project",name)
            update_timeline(name, timeline_mod)
            st.rerun()
    
    with tab_team:
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
        
        if st.button("Save Changes", key="save_team"):
            contacts_mod.insert(0,"project",name)
            update_contracts(name, contacts_mod)
            st.rerun()

    with tab_sheet:

        man_sheet = st.session_state.project["man_sheet"]
        planned_work = st.session_state.project["planned_work"]

        contracts = st.session_state.contracts
        #print(st.session_state.project['man_sheet'])
        if person := st.selectbox("Pessoa", options= st.session_state.project['man_sheet']['person'].unique()):

            sheet = man_sheet[man_sheet['person'] == person].set_index('indicator')

            modifications = st.data_editor(
                sheet.iloc[:7, 1:],
                key = f"{person}_sheet_{st.session_state.key}",
                use_container_width=True
            )
            
            modifications.loc['Horas Trabalhadas'] = modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis'] - modifications.loc['Faltas'] - modifications.loc['Férias']
            modifications.loc['FTE'] = modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis'] - modifications.loc['Férias'])

            if saved_button := st.button("Apply Changes"):
                sheet.update(modifications)
                sheet= sheet.reset_index()
                sheet = sheet.set_index(['person','indicator'])
                
                st.session_state.project["man_sheet"] = st.session_state.project["man_sheet"].set_index(['person','indicator'])
                st.session_state.project["man_sheet"].update(sheet)
                st.session_state.project["man_sheet"] = st.session_state.project["man_sheet"].reset_index()    

            if st.button("Discard Changes"):
                st.session_state.key = (st.session_state.key + 1) % 2
                st.rerun()
           
            st.dataframe(
                modifications.loc[['Horas Trabalhadas', 'FTE']],
                use_container_width=True
            )

            person_work = planned_work[planned_work['person'] == person]

            for wp in planned_work[planned_work['person'] == person]['wp'].unique():

                wp_work = person_work[person_work['wp'] == wp].drop(columns=['trl', 'wp', 'person']).set_index('activity')

                wp_sheet_modifications = st.data_editor(
                    wp_work,
                    key = f"{person}_work_{wp}_{st.session_state.key}",
                    column_config={
                        "activity":st.column_config.TextColumn(
                            wp
                        )
                    }
                )

                person_work = person_work.set_index('activity')
                person_work.update(wp_sheet_modifications, overwrite=True)
                person_work = person_work.reset_index()

            if saved_button:
                st.session_state.project['planned_work'] = st.session_state.project['planned_work'][st.session_state.project['planned_work']['person'] != person]
                st.session_state.project['planned_work'] = pd.concat([st.session_state.project['planned_work'], person_work])

            horas_trabalhaveis = (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).fillna(0)

            float_columns = person_work.select_dtypes(include=['float'])
            sum_wp = person_work[float_columns.columns].sum()

            person_work[float_columns.columns] = ((person_work[float_columns.columns] / sum_wp * modifications.loc['Horas Reais']) / horas_trabalhaveis ).fillna(0)
            if saved_button:
                st.session_state.project['time_allocation'] = st.session_state.project['time_allocation'][st.session_state.project['time_allocation']['person'] != person]
                st.session_state.project['time_allocation'] = pd.concat([st.session_state.project['time_allocation'], person_work])

            cost_activity = person_work.copy()

            cost_activity[float_columns.columns] = person_work[float_columns.columns] * (((modifications.loc['Salário'] * 14) / 11)*(1+(modifications.loc['SS']/100)))
            if saved_button:
                st.session_state.project['cost_allocation'] = st.session_state.project['cost_allocation'][st.session_state.project['cost_allocation']['person'] != person]
                st.session_state.project['cost_allocation'] = pd.concat([st.session_state.project['cost_allocation'], cost_activity])

                st.session_state.projects.iloc[st.session_state.projects['name'] == st.session_state.project_name] = st.session_state.project  
                st.rerun()
            
            st.dataframe(person_work)
            st.dataframe(cost_activity)
            st.dataframe(person_work.drop(columns=['activity', 'person']).groupby(['wp', 'trl']).sum())


    with tab_imputations:

        ftes = st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'FTE']

        ftes = pd.merge(st.session_state.contracts.loc[:,['person','gender']], ftes, on='person', how='left')
        

        st.dataframe(ftes.drop(columns=['person','indicator']).groupby('gender').sum())

        "Atividade / Sum * Horas"

        float_columns = person_work.select_dtypes(include=['float'])
        sum_wp = st.session_state.project["planned_work"][float_columns.columns].sum()
        print(st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Horas Reais'])
        print(st.session_state.project['planned_work'].drop(columns=['trl','activity']).groupby(['wp','person']).sum() / sum_wp)
        
    
if __name__ == "__main__":
    main()
