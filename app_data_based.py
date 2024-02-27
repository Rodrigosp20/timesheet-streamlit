from datetime import timedelta
import datetime
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import numpy as np
import plotly.express as px
import pickle
from utils import *
from st_aggrid import AgGrid

projects_schema = {
    "name": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
    "executed": "datetime64[ns]"
}

activities_schema = {
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
    "profile":"string",
    "gender": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
}

sheets_schema = {
    "person" : "string",
    "date" : "datetime64[ns]",
    "Jornada Diária" : "int64",
    "Dias Úteis": "int64",
    "Faltas" : "float64",
    "Férias" : "float64",
    "Salário" : "float64",
    "SS" : "float64",
    "Custo Aproximado" : "float64",
}

real_work_schema = {
    "person" : "string",
    "project" : "string",
    "date" : "datetime64[ns]",
    "hours" : "int64"
}

planned_work_schema = {
    "person" : "string",
    "project": "string",
    "activity" : "string",
    "date" : "datetime64[ns]",
    "hours" : "int64"
}

def save_data():
    with open('data.pkl', 'wb') as f:
        pickle.dump({
            'activities':st.session_state.activities,
            'contracts':st.session_state.contracts,
            'projects':st.session_state.projects,
            'sheets': st.session_state.sheets,
            'planned_work' : st.session_state.planned_work,
            'real_work' : st.session_state.real_work
        }, f)

def load_file(file):
    if file:
        dfs = pickle.load(file)
        st.session_state.activities= dfs['activities']
        st.session_state.contracts = dfs['contracts']
        st.session_state.projects = dfs['projects']
        st.session_state.sheets = dfs['sheets']
        st.session_state.planned_work = dfs['planned_work']
        st.session_state.real_work = dfs['real_work']
    else:
        st.session_state.activities = pd.DataFrame(columns=activities_schema.keys()).astype(activities_schema)
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)
        st.session_state.sheets = pd.DataFrame(columns=sheets_schema.keys()).astype(sheets_schema)
        st.session_state.planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)
        st.session_state.real_work = pd.DataFrame(columns=real_work_schema.keys()).astype(real_work_schema)

def load_empty_state():

    if 'project' not in st.session_state:
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

def invalid(*args):
    for arg in args:
        if arg is None:
            return True
        
        if type(arg) == str and len(arg) == 0:
            return True
    
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

    if not (project := st.sidebar.selectbox('Select a Project', options = [""] + st.session_state.projects['name'].to_list(), placeholder="Escolhe um projeto")):
        st.title("Criar Projeto")

        project_name = st.text_input("Nome do projeto", key=f"project_name_{st.session_state.key}")
        start_date = st.date_input("Data de inicio", format="DD/MM/YYYY", value=None)
        end_date = st.date_input("Data de encerramento", format="DD/MM/YYYY", value=None, min_value= start_date + timedelta(days=1, weeks=4) if start_date else None)
        
        if st.button("Criar Projeto", disabled= invalid(project_name, start_date, end_date)):
            create_project(project_name, start_date, end_date)
    
    else:

        tab_project, tab_timeline, tab_team, tab_sheet, tab_imputations, tab_costs = st.tabs(["Projeto", "Cronograma", "Equipa", "Pessoal", "Imputação Horas", "Custos"])

        with tab_project:
            st.title(project)

            project = st.session_state.projects.loc[st.session_state.projects['name'] == project].iloc[0]
        
            start_date = st.date_input("Data Inicio", value=project.loc['start_date'], format="DD/MM/YYYY", max_value=project.loc['start_date'])
            end_date = st.date_input("Data Fim", value=project.loc['end_date'], format="DD/MM/YYYY", min_value=project.loc['end_date'])

            if st.button("Save changes", disabled=invalid(start_date, end_date)):
                update_project_dates(project, start_date, end_date)
        
        with tab_timeline:            
            timeline = st.session_state.activities.query("project == @project['name']")
            timeline = timeline.sort_values(by=['wp', 'activity', "start_date"])

            
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
                    
                    if project['executed'] and pd.to_datetime(project['executed']) > wp['real_start_date']:
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

                if project['executed'] and pd.to_datetime(project['executed']) > act.real_start_date:
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
            else:
                st.write('<p style="text-align: center;">Sem Dados Disponíveis</p>', unsafe_allow_html=True)

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
                timeline[['wp', 'activity', 'trl', 'start_date', 'end_date', 'real_start_date', 'real_end_date']],
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
                        min_value=project["start_date"],
                        default=project["start_date"],
                        format="DD/MM/YYYY",
                        required=True
                    ),
                    "end_date": st.column_config.DateColumn(
                        "Data de Termino [Planeada]",
                        max_value=project["end_date"],
                        default=project["end_date"],
                        format="DD/MM/YYYY",
                        required=True
                    ),
                    "real_start_date": st.column_config.DateColumn(
                        "Data de Inicio [Real]",
                        min_value=project["start_date"],
                        default=project["start_date"],
                        format="DD/MM/YYYY",
                        required=True
                    ),
                    "real_end_date": st.column_config.DateColumn(
                        "Data de Termino [Real]",
                        max_value=project["end_date"],
                        default=project["end_date"],
                        format="DD/MM/YYYY",
                        required=True
                    )
                },
                hide_index=True,
                num_rows='dynamic',
                use_container_width=True
            )
            executed_date = st.date_input("Execução", value=project['executed'], min_value=project['start_date'], max_value=project['end_date'])
            timeline_mod['project'] = project['name']

            if st.button("Save Changes"):
                if len(timeline_mod["activity"]) != len(set(timeline_mod["activity"])):
                    st.toast("Duplicate values found in the 'Names' column! Please ensure all values are unique.")
                else:                    
                    update_timeline(project, timeline_mod, executed_date)
                    st.rerun()
       
        with tab_team:
            name = st.session_state.project_name
            contracts = st.session_state.contracts

            project_contracts = contracts[contracts['project'] == name]

            members = st_tags(
                label='Membros do projeto',
                text='Pesquisar',
                value=list(contracts['person']),
                suggestions=list(contracts['person'].unique()),
                key=f"members_{st.session_state.key}"
            )

            updated = project_contracts.loc[project_contracts['person'].isin(members)]
            updated = updated.set_index('person')

            for member in members:

                with st.expander(member):

                    updated.loc[member, 'profile'] = st.text_input("Pefil", key=f"{member}_perfil_{st.session_state.key}", value= updated.loc[member, 'profile'] if member in updated.index else '')
                    updated.loc[member,'gender'] = st.selectbox("Genero", options=["M","F"], key=f"{member}_genero_{st.session_state.key}", index=1 if not pd.isna(gender:=updated.loc[member,'gender']) and gender == 'F' else 0)
                    updated.loc[member,'start_date'] = st.date_input("Data de Inicio",key=f"{member}_inicio_{st.session_state.key}", format="DD/MM/YYYY", value= updated.loc[member,'start_date'] if not pd.isna(updated.loc[member,'start_date']) else project['start_date'], min_value=project['start_date'])
                    updated.loc[member,'end_date'] = st.date_input("Data de Termino",key=f"{member}_fim_{st.session_state.key}", format="DD/MM/YYYY", value= updated.loc[member,'end_date'] if not pd.isna(updated.loc[member,'end_date']) else project['end_date'], max_value=project['end_date'])

            if st.button("Update Members"):
                updated['project'] = st.session_state.project_name
                updated = updated.reset_index()
                
                if updated.eq('').any().any():
                    st.error("Fill form")
                else:
                    update_contracts(project, updated)
                    st.rerun()
            
            if st.button("Discard Changes"):
                st.session_state.key = (st.session_state.key + 1) % 2
                st.rerun()

        with tab_sheet:
            contracts = st.session_state.contracts.query('project == @project["name"]')

            if person := st.selectbox("Selecionar Membro", options= contracts['person'].unique()):
                
                contract = contracts[contracts['person'] == person].iloc[0]

                contract_range = date_range(contract["start_date"],contract["end_date"])
                columns_config = {date : st.column_config.NumberColumn(date, format="%.2f", disabled=True) for date in contract_range }
                
                activities = st.session_state.activities.query('project == @project["name"]')
                sheet = st.session_state.sheets.query('person == @person and date >= @contract["start_date"] and date <= @contract["end_date"]')
                real_work = st.session_state.real_work.query('person == @person and date >= @contract["start_date"] and date <= @contract["end_date"]')
                planned_work = st.session_state.planned_work.query('person == @person and date >= @contract["start_date"] and date <= @contract["end_date"] and project == @project["name"]')
                
                sheet = sheet.merge(real_work.query('project == @project["name"]')[['date', 'hours']], on="date", how="left").rename(columns={'hours':'Horas Reais'})
                sheet = sheet.drop(columns='person').set_index('date')
                sheet.index = sheet.index.strftime('%b/%y')
                sheet = sheet.transpose()

                modifications = st.data_editor(
                    sheet.loc[['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', "Horas Reais"]],
                    key = f"{person}_sheet_{st.session_state.key}",
                    use_container_width=True
                )

                modifications.loc['Salário'] = None
                modifications.loc['SS'] = None
                

                modifications.loc[['Salário','SS']] = st.data_editor(
                    sheet.loc[['Salário', 'SS']],
                    key = f"{person}_mon_sheet_{st.session_state.key}",
                    use_container_width=True
                )
                
                modifications.loc['Horas Trabalhadas'] = modifications.loc['Jornada Diária'].fillna(0) * modifications.loc['Dias Úteis'].fillna(0) - modifications.loc['Faltas'].fillna(0) - modifications.loc['Férias'].fillna(0)
                modifications.loc['FTE'] = (modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis'] - modifications.loc['Férias'])).fillna(0)
                modifications.loc['Custo Aproximado'] =  ( modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).replace(0, np.nan) * modifications.loc['Salário']*14 / 11 * (1 + modifications.loc['SS'] / 100)).fillna(0)

                if saved_button := st.button("Apply Changes"):
                    to_update = modifications.transpose()
                    to_update = to_update.reset_index('date')
                    to_update['date'] = pd.to_datetime(to_update['date'], format='%b/%y')
                    to_update['person'] = person
                    
                    st.session_state.sheets = st.session_state.sheets.query('(person != @person) or (date < @contract["start_date"] or date > @contract["end_date"])')
                    st.session_state.sheets = pd.concat([st.session_state.sheets, to_update[['person', 'date', 'Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Salário', 'SS', 'Custo Aproximado']]])

                    to_update['hours'] = to_update['Horas Reais']
                    to_update['project'] = project['name']
                    st.session_state.real_work = st.session_state.real_work.query('(person != @person) or (project != @project["name"]) or (date < @contract["start_date"] or date > @contract["end_date"])')
                    st.session_state.real_work = pd.concat([st.session_state.real_work, to_update[['person', 'project', 'date', 'hours']]])

                if st.button("Discard Changes", key="sheet_discard"):
                    st.session_state.key = (st.session_state.key + 1) % 2
                    st.rerun()

                st.dataframe(
                    modifications.loc[['Horas Trabalhadas', 'FTE', 'Custo Aproximado']],
                    use_container_width=True,
                    column_config=columns_config
                )

                planned_work = planned_work.merge(activities[['activity', "wp", 'trl']], on="activity", how="left")
                planned_work = planned_work.drop(columns=['person', 'project'])

                wp_sheet = pd.DataFrame(columns=sheet.columns)

                for wp in planned_work['wp'].unique():

                    wp_work = planned_work[planned_work['wp'] == wp]
                    wp_work = wp_work.pivot(index="activity", columns="date", values="hours")
                    wp_work.columns = wp_work.columns.strftime('%b/%y')

                    wp_sheet_modifications = st.data_editor(
                        wp_work,
                        key = f"{person}_work_{wp}_{st.session_state.key}",
                        column_config={
                            "activity":st.column_config.TextColumn(
                                wp
                            )
                        }
                    )

                    wp_sheet = pd.concat([wp_sheet, wp_sheet_modifications])

                other_activities = real_work.query('project != @project["name"] and date >= @contract["start_date"] and date <= @contract["end_date"]')[['date','hours', 'project']]
                other_activities['date'] = other_activities['date'].apply(lambda x: pd.to_datetime(x).strftime('%b/%y'))
                other_activities = other_activities.pivot_table(index='project', columns='date', values='hours')
                df = pd.concat([pd.DataFrame(columns=modifications.columns), other_activities])
                df.loc['Outras Atividades'] = modifications.loc['Horas Trabalhadas'] - df.sum(axis=0) - modifications.loc['Horas Reais'].fillna(0)

                st.dataframe(
                    df.fillna(0)
                )
                
                if saved_button:
                    wp_sheet = wp_sheet.reset_index(names='activity')
                    wp_sheet = wp_sheet.melt(id_vars='activity', var_name='date', value_name='hours')
                    wp_sheet['date'] = pd.to_datetime(wp_sheet['date'], format='%b/%y')
                    wp_sheet['person'] = person
                    wp_sheet['project'] = project['name']

                    st.session_state.planned_work = st.session_state.planned_work.query('(person != @person) or (project != @project["name"]) or (date < @contract["start_date"] or date > @contract["end_date"])')
                    st.session_state.planned_work = pd.concat([st.session_state.planned_work, wp_sheet])
                    st.rerun()

                horas_trabalhaveis = (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).fillna(0)
                sum_wp = wp_sheet.sum()
                
                sum_wp= sum_wp.replace(0, np.nan)
                horas_trabalhaveis = horas_trabalhaveis.replace(0, np.nan)

                wp_sheet = ((wp_sheet / sum_wp * modifications.loc['Horas Reais']) / horas_trabalhaveis ).fillna(0)
                
                st.dataframe(wp_sheet)

                cost_wp = wp_sheet * (((modifications.loc['Salário'] * 14) / 11)* (1+(modifications.loc['SS']/100) ))
  
                st.dataframe(cost_wp)
                
                wp_sheet = wp_sheet.reset_index(names="activity")
                wp_sheet = wp_sheet.merge(activities[['activity', 'wp', 'trl']], on="activity", how="left")

                st.dataframe(wp_sheet.drop(columns=['activity']).groupby(['wp', 'trl']).sum())



        with tab_imputations:
            
            work = st.session_state.real_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
            
            ftes = work.merge(st.session_state.contracts[["person", "project", "gender"]], on=["person", "project"])
            ftes = ftes.merge(st.session_state.sheets[["person", "date", "Jornada Diária", "Dias Úteis", "Férias"]], on=["person", "date"])

            ftes['FTE'] = (ftes['hours'] / (ftes['Jornada Diária'] * ftes['Dias Úteis'] - ftes['Férias']).replace(0, np.nan)).fillna(0)
            ftes = ftes.pivot_table(index='gender', columns='date', values='FTE', aggfunc='sum')
            ftes.columns = ftes.columns.strftime('%b/%y')
        
            st.dataframe(ftes)

            planned_work = st.session_state.planned_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
            planned_work = planned_work.pivot_table(index=['person', 'project'], columns='date', values='hours')
            print(planned_work)
            """
                if not st.session_state.project['man_sheet'].empty:
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
            """

        with tab_costs:
            pass
            #cost_allocation = st.session_state.project['cost_allocation']
            #cost_allocation = cost_allocation.drop(columns=['person', 'activity']).groupby(['wp', 'trl']).sum() 

            #result = cost_allocation.groupby(level='wp').sum()
            #result['trl'] = 'total'
            #result = result.reset_index()
            #result = result.set_index(['wp', 'trl'])
            
            #cost_allocation = pd.concat([cost_allocation, result])
            #st.dataframe(cost_allocation)

       
    
if __name__ == "__main__":
    main()
