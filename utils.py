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

    #Dropping all sheest for now
    st.session_state.project['man_sheet'] = st.session_state.project['man_sheet'].drop(st.session_state.project['man_sheet'].index)
    st.session_state.project['planned_work'] = st.session_state.project['planned_work'].drop(st.session_state.project['planned_work'].index)
    for person in data['person'].to_list():
        create_sheet(person, name)


def create_sheet(person, name):
    man_sheet = st.session_state.project['man_sheet']
    planned_work = st.session_state.project['planned_work']

    new_sheet = pd.DataFrame({'person':person, 'indicator':['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas Reais', 'Salário', 'Horas Trabalhadas', 'FTE']})
    
    st.session_state.project['man_sheet'] = pd.concat([man_sheet, new_sheet], ignore_index=True)
    st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Jornada Diária'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Jornada Diária'].fillna(8)
    st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Salário'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Salário'].fillna(0)
    st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Dias Úteis'] =  st.session_state.project['man_sheet'].loc[st.session_state.project['man_sheet']['indicator'] == 'Dias Úteis'].fillna(22)
    st.session_state.project['man_sheet'] = st.session_state.project['man_sheet'].fillna(0)
    
    timelines = st.session_state.timelines
    project_timeline = timelines[timelines['project'] == name]
    
    new_work= pd.DataFrame({'person': person, 'wp':project_timeline['wp'], 'activity':project_timeline['activity'], 'trl':project_timeline['trl']})
    st.session_state.project['planned_work'] = pd.concat([planned_work, new_work], ignore_index=True)
    st.session_state.project['planned_work'] = st.session_state.project['planned_work'].fillna(0)

def update_sheets():
    for person in st.session_state.project['persons'].itertuples(index=False):

        if person.Nome not in st.session_state.project['sheets'].values():

            person_sheets = {}
            
            start_date = st.session_state.project['start_date']
            end_date = st.session_state.project['end_date']

            months_range = pd.date_range(start=start_date, end=end_date, freq='MS')
            formatted_columns = [month.strftime('%b/%y') for month in months_range]

            df = pd.DataFrame(columns=formatted_columns, index=['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas reais', 'Horas trabalhadas', 'FTE'])
            
            df.loc['Jornada Diária'] = 8
            df.loc['Dias Úteis'] = 20
            df.loc['Faltas'] = 0
            df.loc['Férias'] = 0
            df.loc['Horas reais'] = 0
            
            df.loc['Horas trabalhadas'] = df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Faltas'] - df.loc['Férias']
            df.loc['FTE'] = df.loc['Horas reais'] / (df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Férias'])

            person_sheets['sheet'] = df

            for wp, activites in st.session_state.project['timeline'].items():

                df = pd.DataFrame(columns=['TRL']+formatted_columns, index=activites.keys())
                for act in activites.keys():
                    df.loc[act,'TRL'] = st.session_state.project['timeline'][wp][act]['trl']

                df.loc[:, df.columns != 'TRL'] = 0

                person_sheets[wp] = df
        
        else:
            pass
            #TODO: Modify Dataframe

        st.session_state.project['sheets'][person.Nome] = person_sheets

