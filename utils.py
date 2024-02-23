from datetime import timedelta
import pandas as pd
import streamlit as st
import numpy as np
from itertools import product

def date_range(start, end):
    months_range = pd.date_range(start=start, end=end, freq='MS')
    return [month.strftime('%b/%y') for month in months_range]

def reset_key():
    st.session_state.key = (st.session_state.key + 1) % 2


def create_project(name, start, end):
        
    if not st.session_state.projects[st.session_state.projects['name'] == name].empty:
        return st.error("Projeto já existe")

    st.session_state.projects.loc[len(st.session_state.projects)] = [name, start, end, None]
    reset_key()
    st.rerun()

def update_project_dates(project, start, end):
    if start == project.loc['start_date'] and end == project.loc['end_date']:
        return st.error("Same dATES")

def update_timeline(project, data, executed):
    st.session_state.activities = st.session_state.activities.query('project != @project["name"]')
    st.session_state.activities = pd.concat([st.session_state.activities, data])
    st.session_state.projects.query('name == @project["name"]').loc[0, 'executed'] = executed

    contracts = st.session_state.contracts.query('project == @project["name"]')

    for contract in contracts.itertuples():
        
        contract_range = pd.date_range(start=contract.start_date, end=contract.end_date, freq='MS')
        st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract.start_date and date <= @contract.start_date)')
        
        activities_dates_combinations = list(product(data["activity"], contract_range))
        st.session_state.planned_work = pd.concat([st.session_state.planned_work, pd.DataFrame({"person": contract.person, "project": project['name'], "activity": [item[0] for item in activities_dates_combinations], "date": [item[1] for item in activities_dates_combinations], "hours":0})])

    st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "activity", "date"])
    st.session_state.planned_work = st.session_state.planned_work.query('activity in @data["activity"]')
    
def update_contracts(project, data):
    st.session_state.contracts = st.session_state.contracts.query('project != @project["name"]')
    data['project'] = project['name']
    st.session_state.contracts = pd.concat([st.session_state.contracts, data])

    activities = st.session_state.activities.query('project == @project["name"]')
    
    for contract in data.itertuples():
        contract_range = pd.date_range(start=contract.start_date, end=contract.end_date, freq='MS')

        st.session_state.sheets = pd.concat([st.session_state.sheets, pd.DataFrame({"person": contract.person, "date": contract_range, "Jornada Diária": 8, "Dias Úteis":20, "Faltas": 0, "Férias": 0, "Salário": 0, "SS": 23.75})])

        st.session_state.real_work = st.session_state.real_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract.start_date and date <= @contract.start_date)')
        st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract.start_date and date <= @contract.start_date)')

        st.session_state.real_work = pd.concat([st.session_state.real_work, pd.DataFrame({"person": contract.person, "project":project["name"], "date": contract_range, "hours":0})])
        
        activities_dates_combinations = list(product(activities['activity'], contract_range))
        st.session_state.planned_work = pd.concat([st.session_state.planned_work, pd.DataFrame({"person": contract.person, "project":project["name"], "activity":[item[0] for item in activities_dates_combinations], "date": [item[1] for item in activities_dates_combinations], "hours":0})])

    st.session_state.sheets = st.session_state.sheets.drop_duplicates(subset=["person", "date"])
    st.session_state.real_work = st.session_state.real_work.drop_duplicates(subset=["person", "project", "date"])    
    st.session_state.real_work = st.session_state.real_work.query('(project != @project["name"]) or (person in @data["person"])')    
    st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "project", "activity", "date"])
    st.session_state.planned_work = st.session_state.planned_work.query('(project != @project["name"]) or (person in @data["person"])')
 

