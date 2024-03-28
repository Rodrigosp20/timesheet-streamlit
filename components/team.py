from streamlit_tags import st_tags
import streamlit as st
from utils import *

def update_contracts(project, data):

    activities = st.session_state.activities.query('project == @project["name"]')
    
    for contract in data.itertuples():

        contract_start_date = get_first_date(contract.start_date)
        contract_end_date = get_last_date(contract.end_date)

        contract_range = pd.date_range(start= contract_start_date, end= contract_end_date, freq='MS')

        st.session_state.sheets = pd.concat([st.session_state.sheets, pd.DataFrame({"person": contract.person, "date": contract_range, "Jornada Diária": 8, "Faltas": 0, "Férias": 0, "Salário": 0, "SS": 23.75})])

        st.session_state.real_work = st.session_state.real_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract_start_date and date <= @contract_end_date)')
        st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract_start_date and date <= @contract_end_date)')

        st.session_state.real_work = pd.concat([st.session_state.real_work, pd.DataFrame({"person": contract.person, "project":project["name"], "date": contract_range, "hours":0})])
        
        for act in activities.itertuples(index=False):
            act_range = pd.date_range(start= get_first_date(act.real_start_date), end= get_last_date(act.real_end_date), freq='MS')
            st.session_state.planned_work = pd.concat([st.session_state.planned_work, pd.DataFrame({"person": contract.person, "project":project["name"], "activity":act.activity, "date":act_range, "hours":0})])

    st.session_state.sheets = st.session_state.sheets.drop_duplicates(subset=["person", "date"])
    st.session_state.real_work = st.session_state.real_work.drop_duplicates(subset=["person", "project", "date"])    
    st.session_state.real_work = st.session_state.real_work.query('(project != @project["name"]) or (person in @data["person"])')
    st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "project", "activity", "date"])
    st.session_state.planned_work = st.session_state.planned_work.query('(project != @project["name"]) or (person in @data["person"])')
 
    st.session_state.sheets = st.session_state.sheets.sort_values(by="date")
    st.session_state.planned_work = st.session_state.planned_work.sort_values(by="date")

    st.session_state.contracts = st.session_state.contracts.query('project != @project["name"]')
    st.session_state.contracts = pd.concat([st.session_state.contracts, data])
    st.rerun()

def team_widget(project):
    contracts = st.session_state.contracts
    project_contracts = st.session_state.contracts.query('project == @project["name"]')
    
    updated = st.data_editor(
        project_contracts.set_index("person"),
        key=f"persons_table_{st.session_state.key}",
        column_order=("person", "profile", "gender","start_date","end_date"),
        column_config={
            "person": st.column_config.TextColumn("Pessoa"),
            "profile": st.column_config.TextColumn("Perfil"),
            "gender": st.column_config.SelectboxColumn("Gênero", options=['M', 'F']),
            "start_date": st.column_config.DateColumn("Data de Inicio", format="DD/MM/YYYY", min_value=project["start_date"], max_value=project["end_date"], default=project["start_date"]),
            "end_date": st.column_config.DateColumn("Data de Término", format="DD/MM/YYYY", min_value=project["start_date"], max_value=project["end_date"], default=project["end_date"])
        },
        use_container_width=True,
        num_rows="dynamic"
    )

    # members = st_tags(
    #     label='Membros do projeto',
    #     text='Pesquisar',
    #     value=list(project_contracts['person']),
    #     suggestions=list(contracts['person'].unique()),
    #     key=f"members_{st.session_state.key}"
    # )

    # updated = project_contracts.loc[project_contracts['person'].isin(members)]
    # updated = updated.set_index('person')

    # for member in members:

    #     with st.expander(member, expanded=True):

    #         col1, col2 = st.columns(2)

    #         updated.loc[member, 'profile'] = col1.text_input("Pefil", key=f"{member}_perfil_{st.session_state.key}", value= updated.loc[member, 'profile'] if member in updated.index else '')
    #         updated.loc[member,'gender'] = col2.selectbox("Genero", options=["M","F"], key=f"{member}_genero_{st.session_state.key}", index=1 if not pd.isna(gender:=updated.loc[member,'gender']) and gender == 'F' else 0)
            
    #         col1, col2 = st.columns(2)
    #         updated.loc[member,'start_date'] = col1.date_input("Data de Inicio",key=f"{member}_inicio_{st.session_state.key}", format="DD/MM/YYYY", value= updated.loc[member,'start_date'] if not pd.isna(updated.loc[member,'start_date']) else project['start_date'], min_value=project['start_date'])
    #         updated.loc[member,'end_date'] = col2.date_input("Data de Termino",key=f"{member}_fim_{st.session_state.key}", format="DD/MM/YYYY", value= updated.loc[member,'end_date'] if not pd.isna(updated.loc[member,'end_date']) else project['end_date'], max_value=project['end_date'])

    col1, col2 = st.columns(2)
    if col1.button("Guardar Alterações", use_container_width=True):
        updated['project'] = project['name']
        updated = updated.reset_index()
        
        if updated.eq('').any().any():
            st.error("Fill form")
        else:
            update_contracts(project, updated)
            st.rerun()
    
    if col2.button("Descartar alterações", use_container_width=True):
        st.session_state.key = (st.session_state.key + 1) % 2
        st.rerun()