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
    executed = pd.to_datetime(executed)

    st.session_state.projects.query('name == @project["name"]').loc[0, 'executed'] = executed
    
    contracts = st.session_state.contracts.query('project == @project["name"]')

    if not executed:
        sum_act = st.session_state.planned_work.query('project == @project["name"]').groupby(['person', 'activity'])['hours'].sum()
    else:
        sum_act = st.session_state.planned_work.query('project == @project["name"] and date > @executed').groupby(['person', 'activity'])['hours'].sum()
    

    for act in data.itertuples(index=False):
        project_range = pd.date_range(start= act.real_start_date, end=act.real_end_date, freq="MS")

        if not executed:
            st.session_state.planned_work = st.session_state.planned_work.query('~ (project == @project["name"] and activity == @act.activity)')
        else:
            st.session_state.planned_work = st.session_state.planned_work.query('~ (project == @project["name"] and activity == @act.activity and date > @executed)')


        comb = list(product(contracts['person'], project_range))
        act_df = pd.DataFrame({"person": [item[0] for item in comb], "project": project['name'], "activity": act.activity, "date": [item[1] for item in comb], "hours":0})
        st.session_state.planned_work = pd.concat([st.session_state.planned_work, act_df])
        

    st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "activity", "date"])

    
    for contract in contracts.itertuples():

        st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract.start_date and date <= @contract.end_date)')
        
        for act in data['activity']:
           
            try:
                sum = sum_act.loc[contract.person,act]
            except:
                continue
                
            if executed:
                df = st.session_state.planned_work
                filter = (df['person'] == contract.person) & (df['date'] > executed) & (df['activity'] == act)
            
                st.session_state.planned_work.loc[filter, 'hours'] = sum
                st.session_state.planned_work.loc[filter, 'hours'] = st.session_state.planned_work.loc[filter, 'hours'].div(len(st.session_state.planned_work.loc[filter, 'hours'])) 
            else:
                df = st.session_state.planned_work
                filter = (df['person'] == contract.person) & (df['activity'] == act)

                st.session_state.planned_work.loc[filter, 'hours'] = sum
                st.session_state.planned_work.loc[filter, 'hours'] = st.session_state.planned_work.loc[filter, 'hours'].div(len(st.session_state.planned_work.loc[filter, 'hours']))
    
    st.rerun()
    
def update_contracts(project, data):
    st.session_state.contracts = st.session_state.contracts.query('project != @project["name"]')
    st.session_state.contracts = pd.concat([st.session_state.contracts, data])

    activities = st.session_state.activities.query('project == @project["name"]')
    
    for contract in data.itertuples():
        contract_range = pd.date_range(start=contract.start_date, end=contract.end_date, freq='MS')

        st.session_state.sheets = pd.concat([st.session_state.sheets, pd.DataFrame({"person": contract.person, "date": contract_range, "Jornada Diária": 8, "Dias Úteis":20, "Faltas": 0, "Férias": 0, "Salário": 0, "SS": 23.75})])

        st.session_state.real_work = st.session_state.real_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract.start_date and date <= @contract.end_date)')
        st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract.start_date and date <= @contract.end_date)')

        st.session_state.real_work = pd.concat([st.session_state.real_work, pd.DataFrame({"person": contract.person, "project":project["name"], "date": contract_range, "hours":0})])
        
        activities_dates_combinations = list(product(activities['activity'], contract_range))
        st.session_state.planned_work = pd.concat([st.session_state.planned_work, pd.DataFrame({"person": contract.person, "project":project["name"], "activity":[item[0] for item in activities_dates_combinations], "date": [item[1] for item in activities_dates_combinations], "hours":0})])

    st.session_state.sheets = st.session_state.sheets.drop_duplicates(subset=["person", "date"])
    st.session_state.real_work = st.session_state.real_work.drop_duplicates(subset=["person", "project", "date"])    
    st.session_state.real_work = st.session_state.real_work.query('(project != @project["name"]) or (person in @data["person"])')    
    st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "project", "activity", "date"])
    st.session_state.planned_work = st.session_state.planned_work.query('(project != @project["name"]) or (person in @data["person"])')
 

