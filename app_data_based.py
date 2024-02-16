import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
    "cost_allocation": "object",
    "executed": "datetiem64[ns]"
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
    "real_start_date": "datetime64[ns]",
    "real_end_date": "datetime64[ns]"
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


    tab_project, tab_timeline, tab_team, tab_sheet, tab_imputations, tab_costs = st.tabs(["Projeto", "Cronograma", "Equipa", "Pessoal", "Imputação Horas", "Custos"])

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

        timeline = st.session_state.timelines[st.session_state.timelines['project'] == name]
        
        timeline = timeline.sort_values(by=['wp', 'activity', "start_date"])

        # Group by 'wp' and select min_date_min and max_date_max
        result = timeline.groupby('wp').agg({'start_date': 'min', 'end_date': 'max', 'real_start_date': 'min', 'real_end_date': 'max'})

        gantt_data = []
        last_wp = None
        for act in timeline.itertuples():
            if last_wp != act.wp:
                wp = result.loc[act.wp]
                gantt_data.append({
                    'Task': act.wp,
                    'Start': wp['start_date'],
                    'Finish': wp['end_date'],
                    'Color': "Planeado"
                })

                if wp['start_date'] != wp['real_start_date'] or wp['end_date'] != wp['real_end_date']:
                    gantt_data.append({
                        'Task': act.wp,
                        'Start': wp['real_start_date'],
                        'Finish': wp['real_end_date'],
                        'Color': "Real"
                    })
                
                if st.session_state.project['executed'] and pd.to_datetime(st.session_state.project['executed']) > wp['real_start_date']:
                    gantt_data.append({
                        'Task': act.wp,
                        'Start': wp['real_start_date'],
                        'Finish': st.session_state.project['executed'],
                        'Color': "Executado"
                    })
                
                last_wp = act.wp

            gantt_data.append({
                'Task': act.activity,
                'Start': act.start_date,
                'Finish': act.end_date,
                'Color': f"Planeado"
            })
        
            if act.start_date != act.real_start_date or act.end_date != act.real_end_date:   
                gantt_data.append({
                    'Task': act.activity,
                    'Start': act.real_start_date,
                    'Finish': act.real_end_date,
                    'Color': f"Real"
                })

            if st.session_state.project['executed'] and pd.to_datetime(st.session_state.project['executed']) > act.real_start_date:
                gantt_data.append({
                    'Task': act.activity,
                    'Start': act.real_start_date,
                    'Finish': st.session_state.project['executed'],
                    'Color': "Executado"
                })
        
        if len(gantt_data) > 0:
            gantt_df = pd.DataFrame(gantt_data)

            fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="Color", color_discrete_map={'Planeado':"#0AA3EB", "Real":"#DAF1FC", "Executado":"#878787"}, category_orders={'Color': ["WP","Planeado","Real"]})
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(barmode='group')
            
            st.plotly_chart(fig, use_container_width=True)

        wps = st.data_editor(
            np.array(timeline['wp'].unique()),
            column_config={
                "value": st.column_config.TextColumn(
                    "WP",
                    required = True,
                    validate=".+",
                    default="WP"
                )
            },
            key=f"project_wp_{st.session_state.key}",
            num_rows='dynamic'
        )

        timeline_mod = st.data_editor(
            timeline.iloc[:, 1:],
            column_config={
                "wp": st.column_config.SelectboxColumn(
                    "WP",
                    options=wps,
                    required=True
                ),
                "activity": st.column_config.TextColumn(
                    "Atividade",
                    required=True,
                    default="A"
                ),
                "trl": st.column_config.SelectboxColumn(
                    "TRL",
                    options=['TRL 3-4', 'TRL 5-9'],
                    required=True
                ),
                "start_date": st.column_config.DateColumn(
                    "Data de Inicio [Planeada]",
                    min_value=st.session_state.project["start_date"],
                    default=st.session_state.project["start_date"],
                    format="DD/MM/YYYY",
                    required=True
                ),
                "end_date": st.column_config.DateColumn(
                    "Data de Termino [Planeada]",
                    max_value=st.session_state.project["end_date"],
                    default=st.session_state.project["end_date"],
                    format="DD/MM/YYYY",
                    required=True
                ),
                "real_start_date": st.column_config.DateColumn(
                    "Data de Inicio [Real]",
                    min_value=st.session_state.project["start_date"],
                    default=st.session_state.project["start_date"],
                    format="DD/MM/YYYY",
                    required=True
                ),
                "real_end_date": st.column_config.DateColumn(
                    "Data de Termino [Real]",
                    max_value=st.session_state.project["end_date"],
                    default=st.session_state.project["end_date"],
                    format="DD/MM/YYYY",
                    required=True
                )
            },
            hide_index=True,
            num_rows='dynamic',
            use_container_width=True
        )
        executed_date = st.date_input("Execução", value=st.session_state.project['executed'], min_value=st.session_state.project['start_date'], max_value=st.session_state.project['end_date'])

        if st.button("Save Changes"):
            if len(timeline_mod["activity"]) != len(set(timeline_mod["activity"])):
                st.toast("Duplicate values found in the 'Names' column! Please ensure all values are unique.")
            else:
                st.session_state.project['executed'] = executed_date
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
                column_config={
                    "Mar/24": st.column_config.NumberColumn(
                        format="%dh"
                    )
                },
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


        float_columns = person_work.select_dtypes(include=['float'])
        sum_wp = st.session_state.project["planned_work"][float_columns.columns].sum()

        real_hours = st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Horas Reais']
        hours_allocation = st.session_state.project['planned_work'].drop(columns=['activity']).groupby(['wp', 'trl', 'person']).sum() / sum_wp
        
        for row in hours_allocation.itertuples():
            hours_allocation.loc[row.Index] = hours_allocation.loc[row.Index] * real_hours[real_hours['person'] == row.Index[2]].iloc[0, 2:]

        st.dataframe(hours_allocation.groupby(level=[2,0]).sum())
        st.dataframe(hours_allocation.groupby(level=[2,1]).sum())
        st.dataframe(hours_allocation.groupby(level=0).sum())

    with tab_costs:
        
        cost_allocation = st.session_state.project['cost_allocation']
        cost_allocation = cost_allocation.drop(columns=['person', 'activity']).groupby(['wp', 'trl']).sum() 

        result = cost_allocation.groupby(level='wp').sum()
        result['trl'] = 'total'
        result = result.reset_index()
        result = result.set_index(['wp', 'trl'])
        
        cost_allocation = pd.concat([cost_allocation, result])
        st.dataframe(cost_allocation)

       
    
if __name__ == "__main__":
    main()
