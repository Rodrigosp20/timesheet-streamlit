from typing import Tuple
import streamlit as st
import pandas as pd
import numpy as np
from utils import *


def format_table(df: pd.DataFrame):
    styled_df = df.style.map(
        lambda x: '' if x > 0 else 'color:#FAD0C4;' if x < 0 else 'color:#BFBFBF;')
    return styled_df.format("{:.2f} €")


def get_column_config(columns: pd.Index, extras: list = []):

    config = {col: st.column_config.NumberColumn(
        col, width="small") for col in columns}
    config[''] = st.column_config.TextColumn("", width="medium")
    for ex in extras:
        config[ex] = st.column_config.TextColumn(ex, width="small")

    return config


def add_subtotals(df):
    subtotals = []
    original_df = df.copy()

    # Calculate subtotals for each level
    for level in df.index.names:
        subtotal = df.groupby(level=level).sum()
        subtotal.index = pd.MultiIndex.from_product(
            [[f'Subtotal {level}'], subtotal.index], names=[None, level]
        )
        subtotal = subtotal.reindex(
            pd.MultiIndex.from_product([[f'Subtotal {level}'], subtotal.index.get_level_values(level)],
                                       names=[None, level]), fill_value=np.nan)
        subtotals.append(subtotal)

    # Concatenate the original DataFrame with subtotals
    df_with_subtotals = pd.concat([original_df] + subtotals).sort_index()

    # Fill NaNs with empty strings for display purposes
    df_with_subtotals = df_with_subtotals.reset_index()
    for name in df_with_subtotals.columns[:-3]:
        df_with_subtotals[name] = df_with_subtotals[name].replace({np.nan: ''})

    df_with_subtotals = df_with_subtotals.set_index(df.index.names)

    return df_with_subtotals


@st.cache_data
def get_wp_costs(activities, real_work, planned_work, sheet, iapmei_formula=False):
    planned_work = planned_work.merge(
        activities[["wp", "activity", "trl"]], on="activity", how="left")

    real_work = real_work.pivot_table(
        index="person", columns="date", values="hours")

    planned_work = planned_work.pivot_table(
        index=['person', "wp", "trl", "activity"], columns='date', values='hours', aggfunc="sum")

    total_person_planned_work = planned_work.groupby(level="person").sum()

    sheet['trabalhaveis'] = sheet['Jornada Diária'] * sheet['Dias Úteis']
    sheet['sal'] = (sheet['Salário'] * 14 / 11) * (1 + sheet["SS"]/100)

    sheet = sheet.pivot_table(index="person", columns="date", values=[
                              "trabalhaveis", "sal"])

    affection = planned_work.div(total_person_planned_work.replace(0, np.nan)).mul(
        real_work).div(sheet['trabalhaveis'].replace(0, np.nan)).fillna(0)
    planned_affection = planned_work.div(
        sheet['trabalhaveis'].replace(0, np.nan)).fillna(0)

    planned_cost = planned_affection.groupby(['person', 'wp', 'trl']).sum()
    costs = affection.groupby(['person', 'wp', 'trl']).sum()
    if iapmei_formula:
        costs = costs.applymap(lambda x: floor_map(x, 4))
        planned_cost = planned_cost.applymap(lambda x: floor_map(x, 4))

    costs = costs.mul(sheet['sal'])
    planned_cost = planned_cost.mul(sheet['sal'])

    # costs = affection.mul(sheet['sal'])
    costs.columns = costs.columns.strftime('%b/%y')
    planned_cost.columns = planned_cost.columns.strftime('%b/%y')

    if iapmei_formula:
        planned_cost = planned_cost.applymap(lambda x: floor_map(x, 2))
        costs = costs.applymap(lambda x: floor_map(x, 2))

    wps_costs = costs.groupby(['wp']).sum()
    wp_trl_costs = costs.groupby(['wp', 'trl']).sum()

    if iapmei_formula:
        affection = affection.applymap(lambda x: floor_map(x, 4))

    activity_costs = affection.mul(sheet['sal'])

    if iapmei_formula:
        activity_costs = activity_costs.applymap(lambda x: floor_map(x, 2))
    activity_costs.columns = activity_costs.columns.strftime('%b/%y')

    return activity_costs, wps_costs, wp_trl_costs, planned_cost


def cost_allocation_widget(project):
    work = st.session_state.real_work.query(
        'project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
    work['hours'] = work['hours'].apply(
        pd.to_numeric, errors='coerce').fillna(0)

    planned_work = st.session_state.planned_work.query(
        'project == @project["name"] and date >= @project["start_date"] and date <= @project["end_date"]')
    planned_work['hours'] = planned_work['hours'].apply(
        pd.to_numeric, errors='coerce').fillna(0)

    sheet = st.session_state.sheets.query('person in @work["person"].unique() and date >= @project["start_date"] and date <= @project["end_date"]')[
        ["person", "date", "Jornada Diária", "SS", "Salário"]]
    sheet[["Jornada Diária", "SS", "Salário"]] = sheet[["Jornada Diária",
                                                        "SS", "Salário"]].apply(pd.to_numeric, errors='coerce').fillna(0)

    activities = st.session_state.activities.query(
        'project == @project["name"]')

    working_days = st.session_state.working_days.query(
        'project == @project["name"]')
    working_days['day'] = working_days['day'].apply(
        pd.to_numeric, errors='coerce').fillna(0)

    sheet = sheet.merge(working_days[['date', 'day']], on="date", how="left").rename(
        columns={'day': 'Dias Úteis'})

    get_topbar(project['name'], buttons=False)

    if not planned_work.empty:

        st.subheader("Custos Monetários p/ WP")
        iapmei_formula = st.toggle("Iapmei Formula")

        costs, wps_costs, wp_trl_costs, planned_cost = get_wp_costs(
            activities, work, planned_work, sheet, iapmei_formula)

        for wp, _ in costs.groupby(level='wp'):

            costs_wp = pd.concat(
                [wps_costs.loc[wps_costs.index == wp], wp_trl_costs.xs(wp, level="wp")])

            st.dataframe(
                format_table(costs_wp),
                column_config=get_column_config(costs.columns)
            )

        total = pd.DataFrame(columns=costs.columns)
        total.loc['Total Real'] = wps_costs.sum(axis=0)
        total.loc['Total Planeado'] = planned_cost.sum(axis=0)

        desvio = total.loc['Total Planeado'] - \
            total.loc['Total Real']

        total.loc['Desvio Acumulado'] = desvio.cumsum()

        st.dataframe(
            format_table(total),
            column_config=get_column_config(total.columns)
        )

        costs = costs.sort_index(level=['wp', 'activity']).groupby(
            level=["wp", "activity"]).sum()

        st.dataframe(
            format_table(costs),
            column_config=get_column_config(
                total.columns, extras=['wp', 'activity'])
        )

    sync_dataframes()
