from typing import Tuple
import streamlit as st
import pandas as pd
import numpy as np
from utils import *

def format_table(df: pd.DataFrame):
    styled_df = df.style.map(lambda x: '' if x > 0 else 'color:#BFBFBF;')
    return styled_df.format("{:.2f} €")
    

def get_column_config(columns: pd.Index):

    config = {col: st.column_config.NumberColumn(col, width="small") for col in columns}
    config[''] = st.column_config.TextColumn("", width="medium")

    return config
 
@st.cache_data
def get_wp_costs(activities, work, planned_work, sheet):
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
    return costs, wps_costs, wp_trl_costs

def cost_allocation_widget(project) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    work = st.session_state.real_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
    planned_work = st.session_state.planned_work.query('project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
    sheet = st.session_state.sheets.query('person in @work["person"].unique() and date >= @project["start_date"] and date <= @project["end_date"]')[["person", "date", "Jornada Diária", "SS", "Salário"]]
    activities = st.session_state.activities.query('project == @project["name"]')

    working_days = st.session_state.working_days.query('project == @project["name"]')
    sheet = sheet.merge(working_days[['date', 'day']], on="date", how="left").rename(columns={'day':'Dias Úteis'})
    
    get_topbar(project['name'])
    
    if not planned_work.empty:
        
        costs, wps_costs, wp_trl_costs = get_wp_costs(activities, work, planned_work, sheet)

        st.subheader("Custos Monetários p/ WP")
        for wp, _ in costs.groupby(level='wp'):
            
            st.dataframe(
                format_table(pd.concat([wps_costs.loc[wps_costs.index == wp], wp_trl_costs.xs(wp, level="wp")])),
                column_config=get_column_config(costs.columns)
            )
        
        total = pd.DataFrame(columns=costs.columns)
        total.loc['Total'] = costs.sum(axis=0)
        
        st.dataframe(
            format_table(total),
            column_config=get_column_config(total.columns)
        )
        
    sync_dataframes()