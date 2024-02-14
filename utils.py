import pandas as pd
import streamlit as st
import numpy as np

def date_range(start, end):
    months_range = pd.date_range(start=start, end=end, freq='MS')
    return [month.strftime('%b/%y') for month in months_range]


def update_timeline(name, data):
    st.session_state.timelines = st.session_state.timelines[st.session_state.timelines['project'] != name]
    st.session_state.timelines = pd.concat([st.session_state.timelines, data], ignore_index=True)

def update_contracts(name, data):
    st.session_state.contracts = st.session_state.contracts[st.session_state.contracts['project'] != name]
    st.session_state.contracts = pd.concat([st.session_state.contracts, data], ignore_index=True)

    #Dropping all sheets for now
    st.session_state.project['man_sheet'] = st.session_state.project['man_sheet'].drop(st.session_state.project['man_sheet'].index)
    st.session_state.project['planned_work'] = st.session_state.project['planned_work'].drop(st.session_state.project['planned_work'].index)
    st.session_state.project['time_allocation'] = st.session_state.project['time_allocation'].drop(st.session_state.project['time_allocation'].index)
    st.session_state.project['cost_allocation'] = st.session_state.project['cost_allocation'].drop(st.session_state.project['cost_allocation'].index)
    for person in data['person'].to_list():
        create_sheet(person, name)
   
    st.session_state.projects.iloc[st.session_state.projects['name'] == st.session_state.project_name] = st.session_state.project    
 
def create_sheet(person, name):
    man_sheet = st.session_state.project['man_sheet']
    planned_work = st.session_state.project['planned_work']
    cost_allocation = st.session_state.project['cost_allocation']
    time_allocation = st.session_state.project['time_allocation']
    

    new_sheet = pd.DataFrame({'person':person, 'indicator':['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas Reais', 'Salário', 'SS', 'Horas Trabalhadas',  'FTE']})
    
    st.session_state.project['man_sheet'] = pd.concat([man_sheet, new_sheet], ignore_index=True)
    st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Jornada Diária'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Jornada Diária'].fillna(8)
    st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Dias Úteis'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Dias Úteis'].fillna(22)
    st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'SS'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'SS'].fillna(23.75)
    st.session_state.project['man_sheet'] = st.session_state.project['man_sheet'].fillna(0)
    
    timelines = st.session_state.timelines
    project_timeline = timelines[timelines['project'] == name]
    
    new_work= pd.DataFrame({'person': person, 'wp':project_timeline['wp'], 'activity':project_timeline['activity'], 'trl':project_timeline['trl']})
    st.session_state.project['planned_work'] = pd.concat([planned_work, new_work], ignore_index=True)
    st.session_state.project['planned_work'] = st.session_state.project['planned_work'].fillna(0)
    st.session_state.project['cost_allocation'] = pd.concat([cost_allocation, new_work], ignore_index=True)
    st.session_state.project['cost_allocation'] = st.session_state.project['cost_allocation'].fillna(0)
    st.session_state.project['time_allocation'] = pd.concat([time_allocation, new_work], ignore_index=True)
    st.session_state.project['time_allocation'] = st.session_state.project['time_allocation'].fillna(0)
