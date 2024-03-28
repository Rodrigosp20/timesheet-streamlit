import streamlit as st
from datetime import timedelta
import numpy as np
from utils import * 

def format_zeros(row):
    return 'color:#BFBFBF;' if row == 0 else ''

def highlight_negative(row):
    if row.name == 'Outras Atividades':
        return ['color: #FF6565;' if val < 0 else 'color: white;' for val in row]
    return ['color: white;'] * len(row)

@st.cache_data
def get_column_order(start_date, end_date):
    return [date.strftime('%b/%y') for date in pd.date_range(start=get_first_date(start_date), end= end_date, freq='MS')]

@st.cache_data
def get_float_columns(contract_start_date, contract_end_date):
    contract_range = date_range(contract_start_date,contract_end_date)
    columns_config = {date : st.column_config.NumberColumn(date, format="%.2f", width="small", disabled=True) for date in contract_range }
    activities_config = {date : st.column_config.NumberColumn(date, default=0) for date in contract_range }

    columns_config[""] = st.column_config.TextColumn(width="medium")
    return columns_config

@st.cache_data
def get_disabled_columns(project):
    if project['executed']:
        return [date for date in date_range(project["start_date"], project['executed'])]
    return []

def fetch_data(project, person, contract_start_date, contract_end_date):
    activities = st.session_state.activities.query('project == @project["name"]')
    working_days = st.session_state.working_days.query('project == @project["name"]')
    sheet = st.session_state.sheets.query('person == @person and date >= @contract_start_date and date <= @contract_end_date')
    real_work = st.session_state.real_work.query('person == @person and date >= @contract_start_date and date <= @contract_end_date')
    planned_work = st.session_state.planned_work.query('person == @person and date >= @contract_start_date and date <= @contract_end_date and project == @project["name"]')
    
    sheet = sheet.merge(real_work.query('project == @project["name"]')[['date', 'hours']], on="date", how="left").rename(columns={'hours':'Horas Reais'})
    sheet = sheet.merge(working_days[['date', 'day']], on="date", how="left").rename(columns={'day':'Dias Úteis'})
    sheet = sheet.drop(columns='person').set_index('date')
    sheet.index = sheet.index.strftime('%b/%y')
    sheet = sheet.transpose()
    return sheet, activities, real_work, planned_work


def sheet_widget(project):
    contracts = st.session_state.contracts.query('project == @project["name"]')

    col1, col2 = st.columns([0.7,0.3])
    if person := col1.selectbox("Selecionar Membro", options= contracts['person'].unique()):
        
        col1, col2 = col2.columns(2)

        saved_button = col1.button("Guardar Alterações")
        if col2.button("Descartar Alterações", key="sheet_discard", on_click=reset_key):
            st.rerun()
        
        init, end = st.slider("", min_value=get_first_date(project["start_date"]), max_value=project["end_date"], format="MMMM/YYYY", value=(project["start_date"], project["end_date"]), step=timedelta(weeks=4))
        
        contract = contracts[contracts['person'] == person].iloc[0]
        
        contract_start_date = get_first_date(contract["start_date"])
        contract_end_date = get_first_date(contract["end_date"])

        float_columns = get_float_columns(contract_start_date, contract_end_date)
        disabled_columns = get_disabled_columns(project)
        columns_order = get_column_order(init,end)
        
        sheet, activities, real_work, planned_work = fetch_data(project, person, contract_start_date, contract_end_date)
        
        st.subheader("Folha de Horas") #########

        modifications = st.data_editor(
            sheet.loc[['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', "Horas Reais"]],
            key = f"{person}_sheet_{st.session_state.key}",
            use_container_width=True,
            column_order=columns_order,
            column_config={
                "":st.column_config.TextColumn(
                    width="medium",
                    disabled=True
                )
            },
            disabled=disabled_columns
        )

        modifications.loc['Salário'] = None
        modifications.loc['SS'] = None
        

        st.subheader("Folha Salarial") ########

        modifications.loc[['Salário','SS']] = st.data_editor(
            sheet.loc[['Salário', 'SS']],
            key = f"{person}_mon_sheet_{st.session_state.key}",
            use_container_width=True,
            column_order=columns_order,
            column_config={
                "":st.column_config.TextColumn(
                    width="medium",
                    disabled=True
                )
            },
            disabled=disabled_columns
        )
        
        modifications.loc['Horas Trabalhadas'] = modifications.loc['Jornada Diária'].fillna(0) * modifications.loc['Dias Úteis'].fillna(0) - modifications.loc['Faltas'].fillna(0) - modifications.loc['Férias'].fillna(0)
        modifications.loc['FTE'] = (modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis'] - modifications.loc['Férias']).replace(0, np.nan)).fillna(0)
        modifications.loc['Custo Aproximado'] =  ( modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).replace(0, np.nan) * modifications.loc['Salário']*14 / 11 * (1 + modifications.loc['SS'] / 100)).fillna(0)

        if saved_button:
            to_update = modifications.transpose()
            to_update = to_update.reset_index('date')
            to_update['date'] = pd.to_datetime(to_update['date'], format='%b/%y')
            to_update['person'] = person
            
            st.session_state.sheets = st.session_state.sheets.query('(person != @person) or (date < @contract_start_date or date > @contract_end_date)')
            st.session_state.sheets = pd.concat([st.session_state.sheets, to_update[['person', 'date', 'Jornada Diária', 'Faltas', 'Férias', 'Salário', 'SS', 'Custo Aproximado']]])
            
            to_update['day'] = to_update['Dias Úteis']
            to_update['hours'] = to_update['Horas Reais']
            to_update['project'] = project['name']
            st.session_state.real_work = st.session_state.real_work.query('(person != @person) or (project != @project["name"]) or (date < @contract_start_date or date > @contract_end_date)')
            st.session_state.real_work = pd.concat([st.session_state.real_work, to_update[['person', 'project', 'date', 'hours']]])
            st.session_state.working_days = st.session_state.working_days.query('project != @project["name"] or (date < @contract_start_date or date > @contract_end_date)')
            st.session_state.working_days = pd.concat([st.session_state.working_days, to_update[['project', 'date', 'day']]])

        st.subheader("Sumário") #######

        st.dataframe(
            modifications.loc[['Horas Trabalhadas', 'FTE', 'Custo Aproximado']].style.format("{:.2f}").map(format_zeros),
            use_container_width=True,
            column_order=columns_order,
            column_config=float_columns
        )

        planned_work = planned_work.merge(activities[['activity', "wp", 'trl']], on="activity", how="left")
        planned_work = planned_work.drop(columns=['person', 'project'])
        planned_work = planned_work.sort_values(by="wp")

        wp_sheet = pd.DataFrame(columns=sheet.columns)

        st.subheader("Horas Planeadas")
        for wp in planned_work['wp'].unique():

            wp_work = planned_work[planned_work['wp'] == wp]
            wp_work = wp_work.pivot(index="activity", columns="date", values="hours")
            wp_work.columns = wp_work.columns.strftime('%b/%y')
            wp_sheet_modifications = st.data_editor(
                wp_work,
                key = f"{person}_work_{wp}_{st.session_state.key}",
                column_order=columns_order,
                column_config={
                    "activity":st.column_config.TextColumn(
                        wp,
                        width="medium",
                        disabled=True
                    )
                },
                disabled=disabled_columns
            )
            
            wp_sheet = pd.concat([wp_sheet, wp_sheet_modifications])

        other_activities = real_work.query('date >= @contract_start_date and date <= @contract_end_date')[['date','hours', 'project']]
        other_activities['date'] = other_activities['date'].apply(lambda x: pd.to_datetime(x).strftime('%b/%y'))
        
        editable_activities = other_activities.query('project not in  @st.session_state.projects["name"]').pivot_table(index='project', columns='date', values='hours')
        noneditable_activities = other_activities.query('project in  @st.session_state.projects["name"] and project != @project["name"]').pivot_table(index='project', columns='date', values='hours')

        st.subheader("Outras Atividades")
        df_edit = pd.concat([pd.DataFrame(columns=sheet.columns), editable_activities])
        if df_edit.empty:
            df_edit.loc[""] = 0
        

        with st.expander("Editar Outras Atividades [Não Listadas]"):
            df_edit = st.data_editor(
                df_edit,
                num_rows='dynamic',
                column_order=columns_order,
                column_config={
                    "":st.column_config.TextColumn(
                        "Atividade",
                        width="medium",
                        required=True,
                    )
                }
            )

        df_noedit = pd.concat([pd.DataFrame(columns=sheet.columns), noneditable_activities])
        if not df_noedit.empty:
            with st.expander("Editar Outras Atividades [Listadas]"):
                df_noedit_mod = st.data_editor(
                    df_noedit,
                    column_order=columns_order,
                    column_config={
                        "":st.column_config.TextColumn(
                            "Atividade",
                            width="medium",
                            required=True,
                            disabled=True
                        )
                    }
                )

                df_noedit_mod= df_noedit_mod.fillna(0)
                df_noedit_mod = df_noedit_mod.where(~ df_noedit.isna(), other=None)
                df_noedit = df_noedit_mod
    
    
        df = pd.concat([df_edit.loc[df_edit.index != ""], df_noedit])
        df.loc['Outras Atividades'] = modifications.loc['Horas Trabalhadas'] - df.sum(axis=0) - modifications.loc['Horas Reais'].fillna(0)
        

        df_style = df.style.map(format_zeros)
        df_style = df_style.format("{:.2f}")
        df_style = df_style.apply(highlight_negative ,axis=1)

        st.dataframe(
            df_style,
            column_order=columns_order,
            column_config={
                "": st.column_config.TextColumn(
                    "Atividades",
                    width="medium"
                )
            }
        )

        if saved_button:
            df = df.reset_index(names="project")
            df = df.melt(id_vars="project", var_name="date",  value_name="hours")
            df['date'] = pd.to_datetime(df['date'], format='%b/%y')
            df['person'] = person
            
            df = df.dropna(subset="hours")
            df = df.loc[df['project'] != 'Outras Atividades']

            st.session_state.real_work = st.session_state.real_work.query('~ (person == @person and project != @project["name"] and date >= @contract_start_date and date <= @contract_end_date)')
            st.session_state.real_work = pd.concat([st.session_state.real_work, df])

        if not wp_sheet.empty:

            if saved_button:
                wp_sheet = wp_sheet.reset_index(names='activity')
                wp_sheet = wp_sheet.melt(id_vars='activity', var_name='date', value_name='hours')
                wp_sheet['date'] = pd.to_datetime(wp_sheet['date'], format='%b/%y')
                wp_sheet['person'] = person
                wp_sheet['project'] = project['name']

                st.session_state.planned_work = st.session_state.planned_work.query('(person != @person) or (project != @project["name"]) or (date < @contract_start_date or date > @contract_end_date)')
                st.session_state.planned_work = pd.concat([st.session_state.planned_work, wp_sheet])
                st.rerun()

            horas_trabalhaveis = (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).fillna(0)
            sum_wp = wp_sheet.sum()
            
            sum_wp= sum_wp.replace(0, np.nan)
            horas_trabalhaveis = horas_trabalhaveis.replace(0, np.nan)

            wp_sheet = ((wp_sheet / sum_wp * modifications.loc['Horas Reais']) / horas_trabalhaveis ).fillna(0)
            
            st.subheader("Resumo de Horas")
            with st.expander("Afetação de Horas p/ Atividade"):
                df = wp_sheet * 100
                df = df.style.format("{:.2f} %")
                df = df.map(format_zeros)

                st.dataframe(
                    df,
                    column_config={
                        "":st.column_config.TextColumn(
                            "Atividade",
                            width="medium"
                        )
                    }
                )

            cost_wp = wp_sheet * (((modifications.loc['Salário'] * 14) / 11)* (1+(modifications.loc['SS']/100) ))

            with st.expander("Custo Monetário p/ Atividade"):
                cost_wp = cost_wp.style.format("{:.2f} €")
                cost_wp = cost_wp.map(format_zeros)
                st.dataframe(
                    cost_wp,
                    column_config={
                        "":st.column_config.TextColumn(
                            "Atividade",
                            width="medium"
                        )
                    }
                )
            
            wp_sheet = wp_sheet.reset_index(names="activity")
            wp_sheet = wp_sheet.merge(activities[['activity', 'wp', 'trl']], on="activity", how="left")

            st.subheader("Afetação WP e TRL")
            
            df = wp_sheet.drop(columns=['activity']).groupby(['wp', 'trl']).sum()
            df = df * 100
            df = df.style.format("{:.2f} %")
            df = df.map(format_zeros)

            st.dataframe(
                df,
                column_config={
                    "wp":st.column_config.TextColumn(
                        "WP",
                        width="medium"
                    ),
                    "trl":st.column_config.TextColumn(
                        "TRL",
                        width="small"
                    ),
                }
            )
