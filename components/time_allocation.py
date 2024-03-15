import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def get_ftes_gender(work, contracts, sheets):
    ftes = work.merge(contracts, on=["person", "project"])
    ftes = ftes.merge(sheets, on=["person", "date"])

    ftes['FTE'] = (ftes['hours'] / (ftes['Jornada Diária'] * ftes['Dias Úteis'] - ftes['Férias']).replace(0, np.nan)).fillna(0)
    ftes = ftes.pivot_table(index='gender', columns='date', values='FTE', aggfunc='sum')
    ftes.columns = ftes.columns.strftime('%b/%y')
    
    ftes.index = ftes.index.map(lambda x: 'Masculino' if x == 'M' else 'Feminino')
    ftes.fillna(0, inplace=True)
    
    return ftes 

@st.cache_data
def get_wp_hours(planned_work, activities, work):
    planned_work = planned_work.merge(activities[["wp", "activity", "trl"]], on="activity", how="left")
        
    work= work.pivot_table(index="person", columns="date", values="hours")
    planned_work = planned_work.pivot_table(index=['person', "wp", "trl"], columns='date', values='hours', aggfunc="sum")
    sum_wp = planned_work.groupby(level="person").sum()

    affection = planned_work.div(sum_wp.replace(0,np.nan)).mul(work).fillna(0)      
    affection.columns = affection.columns.strftime('%b/%y')

    return affection

def time_allocation_widget(project):
    work = st.session_state.real_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
    activities = st.session_state.activities.query('project == @project["name"]')
    planned_work = st.session_state.planned_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')

    contracts = st.session_state.contracts[["person", "project", "gender"]]
    sheets = st.session_state.sheets[["person", "date", "Jornada Diária", "Dias Úteis", "Férias"]]

    if not work.empty:
        
        ftes = get_ftes_gender(work, contracts, sheets)
        ftes = ftes.style.map(lambda x: '' if x > 0 else 'color:#BFBFBF;')
        ftes = ftes.format("{:.2f}")

        st.subheader("FTE p/ Género")
        st.dataframe(
            ftes,
            column_config={
                "gender":st.column_config.TextColumn(
                    "Género",
                    width="medium"
                )
            }

        )

        affection = get_wp_hours(planned_work, activities, work)
        styled_df = affection.groupby(level=[1]).sum().style.map(lambda x: '' if x > 0 else 'color:#BFBFBF;')
        styled_df.format("{:.2f}")
        
        st.subheader("Horas p/ WP")
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
            styled_df = pd.concat([person_wp.xs(person, level='person'), person_trl.xs(person, level='person')]).style.map(lambda x: '' if x > 0 else 'color:#BFBFBF;')
            styled_df = styled_df.format("{:.2f}")

            st.dataframe(
                styled_df,
                column_config={
                    "":st.column_config.TextColumn(
                        person,
                        width="medium"
                    )
                }
            )
        
        