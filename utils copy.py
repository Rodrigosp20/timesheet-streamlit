import pandas as pd
import streamlit as st
import numpy as np

def date_range(start, end):
    months_range = pd.date_range(start=start, end=end, freq='MS')
    return [month.strftime('%b/%y') for month in months_range]


def update_timeline(name, data):
    st.session_state.timelines = st.session_state.timelines[st.session_state.timelines['project'] != name]
    st.session_state.timelines = pd.concat([st.session_state.timelines, data], ignore_index=True)
    st.session_state.projects.loc[st.session_state.projects['name'] == st.session_state.project_name, 'executed'] = st.session_state.project['executed']

    st.session_state.project['planned_work'] = st.session_state.project['planned_work'][st.session_state.project['planned_work']['activity'].isin(data['activity'])]

    for act in data.itertuples(index=False):
        
        if act.activity not in st.session_state.project['planned_work']['activity'].unique():
            
            persons = st.session_state.contracts[st.session_state.contracts['project'] == st.session_state.project_name]['person']

            new_sheet = pd.DataFrame({'person': persons, 'wp':act.wp, 'activity':act.activity, 'trl':act.trl})
            st.session_state.project['planned_work'] = pd.concat([st.session_state.project['planned_work'], new_sheet]).fillna(0)

        else:
            start = pd.to_datetime(act.real_start_date).strftime('%b/%y')
            end = pd.to_datetime(act.real_end_date).strftime('%b/%y')

            activity_range = st.session_state.project['planned_work'].columns[st.session_state.project['planned_work'].columns.get_loc(start):st.session_state.project['planned_work'].columns.get_loc(end) + 1]
            
            start = st.session_state.project['start_date'].strftime('%b/%y')
            if st.session_state.project['executed']:
                end = st.session_state.project['executed'].strftime('%b/%y')
                locked_range = st.session_state.project['planned_work'].columns[st.session_state.project['planned_work'].columns.get_loc(start):st.session_state.project['planned_work'].columns.get_loc(end) + 1]
            else:
                locked_range = []

            end = st.session_state.project['end_date'].strftime('%b/%y')
            full_range = st.session_state.project['planned_work'].columns[st.session_state.project['planned_work'].columns.get_loc(start):st.session_state.project['planned_work'].columns.get_loc(end) + 1]

            activity_range = activity_range.difference(locked_range)
            active_range = full_range.difference(locked_range)
            non_active_range = active_range.difference(activity_range)
            #TODO: MISSING CONTRACT RANGE OF EACH MEMBER
            st.session_state.project['planned_work'].loc[st.session_state.project['planned_work']['activity'] == act.activity, activity_range] = st.session_state.project['planned_work'].loc[st.session_state.project['planned_work']['activity'] == act.activity, active_range].sum(axis=1) / len(activity_range)
            st.session_state.project['planned_work'].loc[st.session_state.project['planned_work']['activity'] == act.activity, non_active_range] = 0
            st.session_state.project['planned_work'].loc[st.session_state.project['planned_work']['activity'] == act.activity, 'trl'] = act.trl
    

def update_contracts(data):
    st.session_state.contracts = st.session_state.contracts[st.session_state.contracts['project'] != st.session_state.project_name]
    st.session_state.contracts = pd.concat([st.session_state.contracts, data], ignore_index=True)

    st.session_state.project['man_sheet'] = st.session_state.project['man_sheet'][st.session_state.project['man_sheet']['person'].isin(data['person'])]
    st.session_state.project['planned_work'] = st.session_state.project['planned_work'][st.session_state.project['planned_work']['person'].isin(data['person'])]

    for row in data.itertuples(index=False):
        
        if row.person not in st.session_state.project['man_sheet']['person'].unique():

            man_sheet = st.session_state.project['man_sheet']
            planned_work = st.session_state.project['planned_work']

            new_sheet = pd.DataFrame({'person':row.person, 'indicator':['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas Reais', 'Salário', 'SS', 'Horas Trabalhadas',  'FTE']})
            
            st.session_state.project['man_sheet'] = pd.concat([man_sheet, new_sheet], ignore_index=True)
            st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Jornada Diária'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Jornada Diária'].fillna(8)
            st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Dias Úteis'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Dias Úteis'].fillna(22)
            st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'SS'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'SS'].fillna(23.75)
            st.session_state.project['man_sheet'] = st.session_state.project['man_sheet'].fillna(0)
            
            timelines = st.session_state.timelines
            project_timeline = timelines[timelines['project'] == st.session_state.project_name]
            
            new_work= pd.DataFrame({'person': row.person, 'wp':project_timeline['wp'], 'activity':project_timeline['activity'], 'trl':project_timeline['trl']})
            st.session_state.project['planned_work'] = pd.concat([planned_work, new_work], ignore_index=True)
            st.session_state.project['planned_work'] = st.session_state.project['planned_work'].fillna(0)
        
        else:
            start = st.session_state.project['start_date'].strftime('%b/%y')
            end = st.session_state.project['end_date'].strftime('%b/%y')
            
            full_range = st.session_state.project['man_sheet'].columns[st.session_state.project['man_sheet'].columns.get_loc(start):st.session_state.project['man_sheet'].columns.get_loc(end) + 1]

            start = row.start_date.strftime('%b/%y')
            end = row.end_date.strftime('%b/%y')

            contract_range = st.session_state.project['man_sheet'].columns[st.session_state.project['man_sheet'].columns.get_loc(start):st.session_state.project['man_sheet'].columns.get_loc(end) + 1]

            start = st.session_state.project['start_date'].strftime('%b/%y')
            if st.session_state.project['executed']:
                end = st.session_state.project['executed'].strftime('%b/%y')
                locked_range = st.session_state.project['planned_work'].columns[st.session_state.project['planned_work'].columns.get_loc(start):st.session_state.project['planned_work'].columns.get_loc(end) + 1]
            else:
                locked_range = []

            non_contract_range = full_range.difference(contract_range)
            non_contract_range = non_contract_range.difference(locked_range)
            contract_range = contract_range.difference(locked_range)
          
            st.session_state.project['man_sheet'].loc[(st.session_state.project['man_sheet']['indicator'] == 'Salário') & (st.session_state.project['man_sheet']['person'] == row.person), non_contract_range] =  0
            st.session_state.project['man_sheet'].loc[(st.session_state.project['man_sheet']['indicator'] == 'Horas Reais') & (st.session_state.project['man_sheet']['person'] == row.person), non_contract_range] = 0
            st.session_state.project['planned_work'].loc[st.session_state.project['planned_work']['person'] == row.person, non_contract_range] = 0
        
   
    st.session_state.projects.loc[st.session_state.projects['name'] == st.session_state.project_name, ['man_sheet', 'planned_work']] = st.session_state.project.loc[['man_sheet', 'planned_work']]
 

