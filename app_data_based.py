import base64
from datetime import timedelta
import datetime
from io import BytesIO
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import numpy as np
import plotly.express as px
import pickle
from utils import *

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

    if not (project := st.sidebar.selectbox('Select a Project', options = [""] + st.session_state.projects['name'].to_list(), placeholder="Escolhe um projeto", on_change=reset_key)):
        st.title("Criar Projeto")

        with st.expander("Criar Projeto Vazio"):
            project_name = st.text_input("Nome do projeto", key=f"project_name_{st.session_state.key}")
            start_date = st.date_input("Data de inicio", format="DD/MM/YYYY", value=None)
            end_date = st.date_input("Data de encerramento", format="DD/MM/YYYY", value=None, min_value= start_date + timedelta(days=1, weeks=4) if start_date else None)

            
            if st.button("Criar Projeto", disabled= invalid(project_name, start_date, end_date)):
                create_new_project(project_name, start_date, end_date)
                
        
        with st.expander("Adicionar Projeto Existente"):
            project_name = st.text_input("Nome do projeto", key=f"exist_project_name_{st.session_state.key}")

            if file := st.file_uploader("Timesheet", accept_multiple_files=False, type="xlsx", key=f"file_uploader_{st.session_state.key}"):

                team, activities, sheets, planned_work, real_work, start_date, end_date = read_timesheet(file, project_name)

                st.dataframe(team)

                st.data_editor(
                    activities,
                    column_order=("wp", "activity", "trl","start_date","end_date","real_start_date","real_end_date", "project"),
                    hide_index=True
                )
            
    
                if st.button("Adicionar Projeto", disabled= invalid(project_name, start_date, end_date)):
                    add_project(project_name, start_date, end_date, activities, team, sheets, planned_work, real_work)
    
    else:

        tab_project, tab_timeline, tab_team, tab_sheet, tab_imputations, tab_costs = st.tabs(["Projeto", "Cronograma", "Equipa", "Pessoal", "Imputação Horas", "Custos"])
        
        with tab_project:
            st.title(project)
            project = st.session_state.projects.loc[st.session_state.projects['name'] == project].iloc[0]

            with st.container(border=True): #Date Project Container
                    
                start_date = st.date_input("Data de Inicio", key=f"project_date_initial_{st.session_state.key}", value=project.loc['start_date'], format="DD/MM/YYYY", max_value=project.loc['start_date'])
                end_date = st.date_input("Data de Termino", key=f"project_date_final_{st.session_state.key}", value=project.loc['end_date'], format="DD/MM/YYYY", min_value=project.loc['end_date'])

                _,col2 = st.columns([0.55,0.45])
                col1, col2 = col2.columns(2)

                if col1.button("Guardar Alterações", key="save_project_dates", disabled=invalid(start_date, end_date)):
                    update_project_dates(project, start_date, end_date)

                col2.button("Descartar Alterações", key="discard_project_dates", on_click=reset_key)

            with st.expander("Gerar Folhas de Afetação"):
                start_date, end_date = st.slider(
                    "Selecionar espaço temporal",
                    min_value= project["start_date"],
                    max_value= project["end_date"],
                    value= (project["start_date"], project["end_date"]),
                    format="MM/YYYY"
                )
                
                if st.button("Gerar Excel", use_container_width=True):
                    wb = generate_sheets(project, start_date, end_date)
                
                    virtual_workbook = BytesIO()
                    wb.save(virtual_workbook)
                    virtual_workbook.seek(0)
                    
                    st.download_button(
                        label="Download Excel File",
                        data = virtual_workbook,
                        file_name="sheets.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with st.expander("Gerar Folhas de Pagamentos"):
                start_date, end_date = st.slider(
                    "Selecionar espaço temporal",
                    min_value= project["start_date"],
                    max_value= project["end_date"],
                    value= (project["start_date"], project["end_date"]),
                    format="MM/YYYY",
                    key="slider_pay"
                )

                if template := st.file_uploader("Template", type=".xlsx", accept_multiple_files=False):
                    df_team = pd.read_excel(template ,sheet_name="Referências", usecols="H", header=3, names=["tecnico"]).dropna()
                    df_team['equipa'] = None

                    df_team = st.data_editor(
                        df_team,
                        column_config={
                            "equipa":st.column_config.SelectboxColumn(
                                "equipa",
                                options=st.session_state.contracts.query('project == @project["name"]')["person"].unique()
                            )
                        },
                        disabled=["tecnico"],
                        use_container_width=True,
                        hide_index=True
                    )

                    df_trl = pd.read_excel(template, sheet_name="Referências", usecols="E", header=3, names=["investimento"]).dropna()
                    df_trl['wp'] = None
                    df_trl['trl'] = None

                    df_trl = st.data_editor(
                        df_trl,
                        column_config={
                            "wp":st.column_config.SelectboxColumn(
                                "wp",
                                options=st.session_state.activities.query('project == @project["name"]')['wp'].unique()
                            ),
                            "trl":st.column_config.SelectboxColumn(
                                "trl",
                                options=st.session_state.activities.query('project == @project["name"]')['trl'].unique()
                            ),
                        },
                        disabled=['investimento'],
                        hide_index=True,
                        use_container_width=True
                    )                    

                    if st.button("Gerar Excel", key="pay_excel", use_container_width=True):
                        wb = generate_pay_sheets(project, template, start_date, end_date, df_team, df_trl)

                        virtual_workbook = BytesIO()
                        wb.save(virtual_workbook)
                        virtual_workbook.seek(0)

                        st.download_button(
                            label="Download Excel File",
                            data = virtual_workbook,
                            file_name="sheets.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
        
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
                    'Color': "Planeado"
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
            
            
            st.subheader("Timeline")
            if len(gantt_data) > 0:
                gantt_df = pd.DataFrame(gantt_data)

                fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="Color", color_discrete_map={'Planeado':"#0AA3EB", "Real":"#DAF1FC", "Executado":"#878787"}, category_orders={'Color': ["WP","Planeado","Real"]})
                fig.update_yaxes(autorange="reversed")
                if len(fig.data) > 1:
                    fig.data[1].width = 0.5
                #fig.update_layout(barmode='group')
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write('<p style="text-align: center;">Sem Dados Disponíveis</p>', unsafe_allow_html=True)
            
            st.subheader("WPs do Projeto")
            wps = st_tags(
                label='',
                text='Inserir',
                value=list(timeline['wp'].unique()),
                suggestions=list(timeline['wp'].unique()),
                key=f"wps_{st.session_state.key}"
            )

            activities = timeline.query('wp in @wps')
            activities = activities.set_index('activity')
            
            to_update = pd.DataFrame(columns=activities.columns)
            st.subheader("Atividades do Projeto")
            for wp in wps:

                with st.expander(wp):                    
                    wp_df = activities.query('wp == @wp')

                    wp_acts = st.data_editor(
                        wp_df,
                        key=f"{wp}_data_{st.session_state.key}",
                        column_order=["activity", "trl", "start_date", "end_date", "real_start_date", "real_end_date"],
                        column_config={
                            "activity": st.column_config.TextColumn(
                                "Atividade",
                                required=True,
                                default="A",
                                width="medium",
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
                                min_value=project["start_date"] if not project['executed'] else project['executed'],
                                max_value=project["end_date"],
                                default=project["start_date"],
                                format="DD/MM/YYYY",
                                required=True
                            ),
                            "real_end_date": st.column_config.DateColumn(
                                "Data de Termino [Real]",
                                min_value=project["start_date"] if not project['executed'] else project['executed'],
                                max_value=project["end_date"],
                                default=project["end_date"],
                                format="DD/MM/YYYY",
                                required=True
                            )
                        },
                        use_container_width=True,
                        num_rows='dynamic'
                    )
                    wp_acts[['wp', 'project']] = [wp, project['name']]
                    to_update = pd.concat([to_update, wp_acts])
                    
            col1 , col2 = st.columns(2)
            
            executed_date = col1.date_input("Execução", value=project['executed'], min_value=project['start_date'], max_value=project['end_date'], format="DD/MM/YYYY")
            to_adjust  = col2.toggle("Ajuste Automático das Horas Planeadas")
            
            col1, col2 = st.columns(2)

            if col1.button("Guardar Alterações", key="save_timeline", use_container_width=True):                  
                update_timeline(project, to_update.reset_index(names="activity"), executed_date, to_adjust)
            
            col2.button("Descartar Alterações", key="discard_timeline", on_click=reset_key, use_container_width=True)
       
        with tab_team:
            contracts = st.session_state.contracts
            project_contracts = st.session_state.contracts.query('project == @project["name"]')
            
            members = st_tags(
                label='Membros do projeto',
                text='Pesquisar',
                value=list(project_contracts['person']),
                suggestions=list(contracts['person'].unique()),
                key=f"members_{st.session_state.key}"
            )

            updated = project_contracts.loc[project_contracts['person'].isin(members)]
            updated = updated.set_index('person')

            for member in members:

                with st.expander(member, expanded=True):

                    col1, col2 = st.columns(2)

                    updated.loc[member, 'profile'] = col1.text_input("Pefil", key=f"{member}_perfil_{st.session_state.key}", value= updated.loc[member, 'profile'] if member in updated.index else '')
                    updated.loc[member,'gender'] = col2.selectbox("Genero", options=["M","F"], key=f"{member}_genero_{st.session_state.key}", index=1 if not pd.isna(gender:=updated.loc[member,'gender']) and gender == 'F' else 0)
                    
                    col1, col2 = st.columns(2)
                    updated.loc[member,'start_date'] = col1.date_input("Data de Inicio",key=f"{member}_inicio_{st.session_state.key}", format="DD/MM/YYYY", value= updated.loc[member,'start_date'] if not pd.isna(updated.loc[member,'start_date']) else project['start_date'], min_value=project['start_date'])
                    updated.loc[member,'end_date'] = col2.date_input("Data de Termino",key=f"{member}_fim_{st.session_state.key}", format="DD/MM/YYYY", value= updated.loc[member,'end_date'] if not pd.isna(updated.loc[member,'end_date']) else project['end_date'], max_value=project['end_date'])

            if st.button("Update Members"):
                updated['project'] = project['name']
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

            col1, col2 = st.columns([0.7,0.3])
            if person := col1.selectbox("Selecionar Membro", options= contracts['person'].unique()):
                
                col1, col2 = col2.columns(2)

                saved_button = col1.button("Guardar Alterações")
                col2.button("Descartar Alterações", key="sheet_discard", on_click=reset_key)

                contract = contracts[contracts['person'] == person].iloc[0]
                
                contract_start_date = get_first_date(contract["start_date"])
                contract_end_date = get_first_date(contract["end_date"])

                contract_range = date_range(contract_start_date,contract_end_date)
                columns_config = {date : st.column_config.NumberColumn(date, format="%.2f", width="small", disabled=True) for date in contract_range }
                activities_config = {date : st.column_config.NumberColumn(date, default=0) for date in contract_range }

                if project['executed']:
                    disabled_cols = [date for date in date_range(project["start_date"], project['executed'])]
                else:
                    disabled_cols = []

                columns_config[""] = st.column_config.TextColumn(width="medium")
                activities_config[""] = st.column_config.TextColumn("Atividades", width="medium", required=True)
                
                activities = st.session_state.activities.query('project == @project["name"]')
                sheet = st.session_state.sheets.query('person == @person and date >= @contract_start_date and date <= @contract_end_date')
                real_work = st.session_state.real_work.query('person == @person and date >= @contract_start_date and date <= @contract_end_date')
                planned_work = st.session_state.planned_work.query('person == @person and date >= @contract_start_date and date <= @contract_end_date and project == @project["name"]')
                
                sheet = sheet.merge(real_work.query('project == @project["name"]')[['date', 'hours']], on="date", how="left").rename(columns={'hours':'Horas Reais'})
                sheet = sheet.drop(columns='person').set_index('date')
                sheet.index = sheet.index.strftime('%b/%y')
                sheet = sheet.transpose()

                st.subheader("Folha de Horas")

                modifications = st.data_editor(
                    sheet.loc[['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', "Horas Reais"]],
                    key = f"{person}_sheet_{st.session_state.key}",
                    use_container_width=True,
                    column_config={
                        "":st.column_config.TextColumn(
                            width="medium",
                            disabled=True
                        )
                    },
                    disabled=disabled_cols
                )

                modifications.loc['Salário'] = None
                modifications.loc['SS'] = None
                

                st.subheader("Folha Salarial")

                modifications.loc[['Salário','SS']] = st.data_editor(
                    sheet.loc[['Salário', 'SS']],
                    key = f"{person}_mon_sheet_{st.session_state.key}",
                    use_container_width=True,
                    column_config={
                        "":st.column_config.TextColumn(
                            width="medium",
                            disabled=True
                        )
                    },
                    disabled=disabled_cols
                )
                
                modifications.loc['Horas Trabalhadas'] = modifications.loc['Jornada Diária'].fillna(0) * modifications.loc['Dias Úteis'].fillna(0) - modifications.loc['Faltas'].fillna(0) - modifications.loc['Férias'].fillna(0)
                modifications.loc['FTE'] = (modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis'] - modifications.loc['Férias']).replace(0, np.nan)).fillna(0)
                modifications.loc['Custo Aproximado'] =  ( modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).replace(0, np.nan) * modifications.loc['Salário']*14 / 11 * (1 + modifications.loc['SS'] / 100)).fillna(0)

                if saved_button:
                    to_update = modifications.transpose()
                    to_update = to_update.reset_index('date')
                    to_update['date'] = pd.to_datetime(to_update['date'], format='%b/%y')
                    to_update['person'] = person
                    
                    st.session_state.sheets = st.session_state.sheets.query('(person != @person) or (date < @contract_start_date or date > @contract_end_date)')
                    st.session_state.sheets = pd.concat([st.session_state.sheets, to_update[['person', 'date', 'Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Salário', 'SS', 'Custo Aproximado']]])

                    to_update['hours'] = to_update['Horas Reais']
                    to_update['project'] = project['name']
                    st.session_state.real_work = st.session_state.real_work.query('(person != @person) or (project != @project["name"]) or (date < @contract_start_date or date > @contract_end_date)')
                    st.session_state.real_work = pd.concat([st.session_state.real_work, to_update[['person', 'project', 'date', 'hours']]])

                st.subheader("Sumário")
                st.dataframe(
                    modifications.loc[['Horas Trabalhadas', 'FTE', 'Custo Aproximado']],
                    use_container_width=True,
                    column_config=columns_config
                )

                planned_work = planned_work.merge(activities[['activity', "wp", 'trl']], on="activity", how="left")
                planned_work = planned_work.drop(columns=['person', 'project'])
                planned_work = planned_work.sort_values(by="wp")

                wp_sheet = pd.DataFrame(columns=sheet.columns)

                st.subheader("Horas Planeadas")

                for wp in planned_work['wp'].unique():

                    wp_work = planned_work[planned_work['wp'] == wp]
                    wp_work = wp_work.pivot(index="activity", columns="date", values="hours")
                    wp_work.columns = wp_work.columns.strftime('%b/%y')

                    wp_sheet_modifications = st.data_editor(
                        wp_work,
                        key = f"{person}_work_{wp}_{st.session_state.key}",
                        column_config={
                            "activity":st.column_config.TextColumn(
                                wp,
                                width="medium",
                                disabled=True
                            )
                        },
                        disabled=disabled_cols
                    )
                    
                    wp_sheet = pd.concat([wp_sheet, wp_sheet_modifications])

                other_activities = real_work.query('date >= @contract_start_date and date <= @contract_end_date')[['date','hours', 'project']]
                other_activities['date'] = other_activities['date'].apply(lambda x: pd.to_datetime(x).strftime('%b/%y'))
                
                editable_activities = other_activities.query('project not in  @st.session_state.projects["name"]').pivot_table(index='project', columns='date', values='hours')
                noneditable_activities = other_activities.query('project in  @st.session_state.projects["name"] and project != @project["name"]').pivot_table(index='project', columns='date', values='hours')

                st.subheader("Resumo de Horas")
                df_edit = pd.concat([pd.DataFrame(columns=sheet.columns), editable_activities])
                if df_edit.empty:
                    df_edit.loc[""] = 0
                

                with st.expander("Editar Outras Atividades [Não Listadas]"):
                    df_edit = st.data_editor(
                        df_edit,
                        num_rows='dynamic',
                        column_config=activities_config
                    )

                df_noedit = pd.concat([pd.DataFrame(columns=sheet.columns), noneditable_activities])
                if not df_noedit.empty:
                    with st.expander("Editar Outras Atividades [Listadas]"):
                        df_noedit_mod = st.data_editor(
                            df_noedit,
                            column_config={
                                "":st.column_config.TextColumn(
                                    "Atividade",
                                    width="medium",
                                    required=True,
                                    disabled=True
                                )
                            }
                        )

                        df_noedit_mod= df_noedit_mod.fillna(0)
                        df_noedit_mod = df_noedit_mod.where(~ df_noedit.isna(), other=None)
                        df_noedit = df_noedit_mod
            
            
                df = pd.concat([df_edit.loc[df_edit.index != ""], df_noedit])
                df.loc['Outras Atividades'] = modifications.loc['Horas Trabalhadas'] - df.sum(axis=0) - modifications.loc['Horas Reais'].fillna(0)

                st.dataframe(
                    df,
                    column_config={
                        "": st.column_config.TextColumn(
                            "Atividades",
                            width="medium"
                        )
                    }
                )

                if saved_button:
                    df = df.reset_index(names="project")
                    df = df.melt(id_vars="project", var_name="date",  value_name="hours")
                    df['date'] = pd.to_datetime(df['date'], format='%b/%y')
                    df['person'] = person
                    
                    df = df.dropna(subset="hours")
                    df = df.loc[df['project'] != 'Outras Atividades']
                    
                    st.session_state.real_work = st.session_state.real_work.query('~(person == @person and project in @df["project"].unique() and date >= @contract_start_date and date <= @contract_end_date)')
                    st.session_state.real_work = pd.concat([st.session_state.real_work, df])

                if not wp_sheet.empty:

                    if saved_button:
                        wp_sheet = wp_sheet.reset_index(names='activity')
                        wp_sheet = wp_sheet.melt(id_vars='activity', var_name='date', value_name='hours')
                        wp_sheet['date'] = pd.to_datetime(wp_sheet['date'], format='%b/%y')
                        wp_sheet['person'] = person
                        wp_sheet['project'] = project['name']

                        st.session_state.planned_work = st.session_state.planned_work.query('(person != @person) or (project != @project["name"]) or (date < @contract_start_date or date > @contract_end_date)')
                        st.session_state.planned_work = pd.concat([st.session_state.planned_work, wp_sheet])
                        st.rerun()

                    horas_trabalhaveis = (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).fillna(0)
                    sum_wp = wp_sheet.sum()
                    
                    sum_wp= sum_wp.replace(0, np.nan)
                    horas_trabalhaveis = horas_trabalhaveis.replace(0, np.nan)

                    wp_sheet = ((wp_sheet / sum_wp * modifications.loc['Horas Reais']) / horas_trabalhaveis ).fillna(0)
                    
                    with st.expander("Afetação de Horas p/ Atividade"):
                        st.dataframe(wp_sheet)

                    cost_wp = wp_sheet * (((modifications.loc['Salário'] * 14) / 11)* (1+(modifications.loc['SS']/100) ))

                    with st.expander("Custo Monetário p/ Atividade"):
                        st.dataframe(cost_wp)
                    
                    wp_sheet = wp_sheet.reset_index(names="activity")
                    wp_sheet = wp_sheet.merge(activities[['activity', 'wp', 'trl']], on="activity", how="left")

                    st.subheader("Afetação WP e TRL")
                    def highlight_positive(val):
                        color = '#2e9aff' if val > 0 else 'white'
                        return f'color: {color};'
                    st.dataframe(wp_sheet.drop(columns=['activity']).groupby(['wp', 'trl']).sum().style.applymap(highlight_positive))

        with tab_imputations:
            
            work = st.session_state.real_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
            
            if not work.empty:
                ftes = work.merge(st.session_state.contracts[["person", "project", "gender"]], on=["person", "project"])
                ftes = ftes.merge(st.session_state.sheets[["person", "date", "Jornada Diária", "Dias Úteis", "Férias"]], on=["person", "date"])

                ftes['FTE'] = (ftes['hours'] / (ftes['Jornada Diária'] * ftes['Dias Úteis'] - ftes['Férias']).replace(0, np.nan)).fillna(0)
                ftes = ftes.pivot_table(index='gender', columns='date', values='FTE', aggfunc='sum')
                ftes.columns = ftes.columns.strftime('%b/%y')
                
                ftes.index = ftes.index.map(lambda x: 'Masculino' if x == 'M' else 'Feminino')
                ftes.fillna(0, inplace=True)

                styled_df = ftes.style.map(lambda x: '' if x > 0 else 'color:#BFBFBF;')
                styled_df = styled_df.format("{:.2f}")

                st.subheader("FTE p/ Género")
                st.dataframe(
                    styled_df,
                    column_config={
                        "gender":st.column_config.TextColumn(
                            "Género",
                            width="medium"
                        )
                    }

                )

                
                activities = st.session_state.activities.query('project == @project["name"]')
                planned_work = st.session_state.planned_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
                planned_work = planned_work.merge(activities[["wp", "activity", "trl"]], on="activity", how="left")
                
                work= work.pivot_table(index="person", columns="date", values="hours")
                planned_work = planned_work.pivot_table(index=['person', "wp", "trl"], columns='date', values='hours', aggfunc="sum")
                sum_wp = planned_work.groupby(level="person").sum()

                affection = planned_work.div(sum_wp.replace(0,np.nan)).mul(work).fillna(0)      
                affection.columns = affection.columns.strftime('%b/%y')
                #st.dataframe(affection)
                st.subheader("Horas p/ WP")

                styled_df = affection.groupby(level=[1]).sum().style.map(lambda x: '' if x > 0 else 'color:#BFBFBF;')
                styled_df = styled_df.format("{:.2f}")
                st.dataframe(
                    styled_df,
                    column_config={
                        "wp":st.column_config.TextColumn(
                            "WP",
                            width="medium"
                        )
                    }
                )
                

                st.subheader("Horas p/ Perfil")
                person_wp = affection.groupby(level=[0,1]).sum()   
                person_trl = affection.groupby(level=[2,0]).sum()          

                for person, _ in person_wp.groupby(level='person'):
                    df = pd.concat([person_wp.xs(person, level='person'), person_trl.xs(person, level='person')])
                    st.dataframe(
                        df,
                        column_config={
                            "":st.column_config.TextColumn(
                                person,
                                width="medium"
                            )
                        }
                    )
                
                
                #st.dataframe(affection.groupby(level=0).sum())
            
        with tab_costs:
            work = st.session_state.real_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
            planned_work = st.session_state.planned_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
            sheet = st.session_state.sheets.query('person in @work["person"].unique() and date >= @project["start_date"] and date <= @project["end_date"]')[["person", "date", "Jornada Diária", "Dias Úteis", "SS", "Salário"]]

            if not planned_work.empty:
                planned_work = planned_work.merge(activities[["wp", "activity", "trl"]], on="activity", how="left")
                
                work= work.pivot_table(index="person", columns="date", values="hours")
                planned_work = planned_work.pivot_table(index=['person', "wp", "trl"], columns='date', values='hours', aggfunc="sum")
                sum_wp = planned_work.groupby(level="person").sum()

                sheet['trabalhaveis'] = sheet['Jornada Diária'] * sheet['Dias Úteis']
                sheet['sal'] = (sheet['Salário'] *14/ 11) * (1 + sheet["SS"]/100)
                sheet = sheet.pivot_table(index="person", columns="date", values=["trabalhaveis", "sal"])

                affection = planned_work.div(sum_wp.replace(0, np.nan)).mul(work).div(sheet['trabalhaveis'].replace(0, np.nan)).fillna(0)

                costs = affection.mul(sheet['sal'])
                costs.columns = costs.columns.strftime('%b/%y')

                wps_costs = costs.groupby(['wp']).sum()
                wp_trl_costs = costs.groupby(['wp', 'trl']).sum()
                st.subheader("Custos Monetários p/WP")
                for wp, _ in costs.groupby(level='wp'):
                    st.dataframe(
                        pd.concat([wps_costs.loc[wps_costs.index == wp], wp_trl_costs.xs(wp, level="wp")]),
                    )
            
       
    
if __name__ == "__main__":
    main()
