from streamlit_tags import st_tags
import streamlit as st
from utils import *

def update_contracts(project, data):

    activities = st.session_state.activities.query('project == @project["name"]')

    data['start_date'] = pd.to_datetime(data['start_date']).dt.date
    data['end_date'] = pd.to_datetime(data['end_date']).dt.date
    
    #check contract dates
    if (data['start_date'] >= data['end_date']).any():
        return set_notification("error", "Contratos com datas inválidas!")
    
    #check if dataframe is complete
    if data.isnull().values.any() or (data == '').values.any():
        return set_notification("error", "Campos em falta!")
    
    if data['person'].nunique() != len(data):
       return set_notification("error", "Funcionários não devem aparecer repetidos") 
    
    data = pd.merge(data, st.session_state.persons, 
                    left_on='person', right_on='name', how='left', suffixes=('', ''))

    data.drop(columns=['name'], inplace=True)

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
    
    set_notification("success", "Equipa do projeto ataulizado com sucesso", force_reset=True)

def team_widget(project):

    save, undo = get_topbar(project['name'])
    
    project_contracts = st.session_state.contracts.query('project == @project["name"]')
    
    st.subheader("Equipa do Projeto")
    
    updated = st.data_editor(
        project_contracts.set_index("person")[['profile','start_date','end_date']],
        key=f"persons_table_{st.session_state.key}",
        column_order=("person", "profile","start_date","end_date"),
        column_config={
            "person": st.column_config.SelectboxColumn("Funcionário", options=st.session_state.persons["name"]),
            "profile": st.column_config.TextColumn("Perfil"),
            "start_date": st.column_config.DateColumn("Data de Inicio", format="DD/MM/YYYY", min_value=project["start_date"], max_value=project["end_date"], default=project["start_date"]),
            "end_date": st.column_config.DateColumn("Data de Conclusão", format="DD/MM/YYYY", min_value=project["start_date"], max_value=project["end_date"], default=project["end_date"])
        },
        use_container_width=True,
        num_rows="dynamic"
    )

    if save:
        updated['project'] = project['name']
        updated = updated.reset_index()
        
        update_contracts(project, updated)
    
    if undo:
        reset_key()