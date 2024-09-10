import streamlit as st
from streamlit_tags import st_tags
import streamlit_antd_components as sac
from datetime import timedelta, datetime
import numpy as np
from utils import * 

def format_zeros_and_negatives(row):
    return 'color:#BFBFBF;' if row == 0 else 'color: #FF6565;' if row < 0 else ''

def format_zeros(row):
    return 'color:#BFBFBF;' if row == 0 else ''

def highlight_negative(row):
    if row.name == 'Outras Atividades':
        return ['color: #FF6565;' if val < 0 else 'color: white;' for val in row]
    return ['color: white;'] * len(row)

def get_dataframe_key(*args):
    return  "_".join(args) + str(st.session_state.key)
 
@st.cache_data
def get_column_order(start_date, end_date):
    return [date.strftime('%b/%y') for date in pd.date_range(start=get_first_date(start_date), end= end_date, freq='MS')]

@st.cache_data
def get_columns_config(contract_start_date, contract_end_date, number_type : Literal['Float', 'Integer'], df_title = "", header = ""):
    contract_range = date_range(contract_start_date,contract_end_date)

    columns_config = {date : st.column_config.NumberColumn(date, format="%.0f" if number_type == 'Integer' else "%.2f", width="small") for date in contract_range }
    columns_config[df_title] = st.column_config.TextColumn(header, width="medium", disabled=True)

    return columns_config

@st.cache_data
def get_disabled_columns(project):
    if project['executed']:
        return [date for date in date_range(project["start_date"], project['executed'])]
    return []

@st.cache_data
def get_salary_table(data):
    df = {"Data":[], "Salário":[], "SS":[]}

    previous_value = -1

    # Iterate over the DataFrame
    for col in data:
        value = data[col].loc['Salário']

        if value != previous_value:
            df['Data'].append(col)
            df['Salário'].append(value)
            df["SS"].append(data[col].loc["SS"])

        previous_value = value

    # Create a new DataFrame with the first date of each sequence
    df =  pd.DataFrame(df)
    df["Data"] = pd.to_datetime(df["Data"], format="%b/%y")
    return df

def fetch_data(project, person, start_date, end_date):
    activities = st.session_state.activities.query('project == @project["name"]')
    working_days = st.session_state.working_days.query('project == @project["name"]')

    sheet = st.session_state.sheets.query('person == @person and date >= @start_date and date <= @end_date')
    real_work = st.session_state.real_work.query('person == @person and date >= @start_date and date <= @end_date')
    planned_work = st.session_state.planned_work.query('person == @person and date >= @start_date and date <= @end_date and project == @project["name"]')
    
    sheet = sheet.merge(real_work.query('project == @project["name"]')[['date', 'hours']], on="date", how="left").rename(columns={'hours':'Horas Reais'})
    sheet = sheet.merge(working_days[['date', 'day']], on="date", how="left").rename(columns={'day':'Dias Úteis'})
    sheet = sheet.drop(columns='person').set_index('date')
    sheet.index = sheet.index.strftime('%b/%y')
    
    sheet = sheet.transpose()
    return sheet, activities, real_work, planned_work

def sheet_widget(project):

    contracts = st.session_state.contracts.query('project == @project["name"]')

    save, undo = get_topbar(project['name'])

    if undo:
        reset_key()

    if person := st.selectbox("Selecionar Membro", options= contracts['person'].unique()):

        st.markdown("""
            <style>
                label[data-baseweb='checkbox'] {
                    width:fit-content;
                }  
            </style>
        """, unsafe_allow_html=True)
        
        #Filter Start and End date
       
        filter_start, filter_end = st.slider("", min_value=get_first_date(project["start_date"]), max_value=get_first_date(project["end_date"]), format="MMMM/YYYY", value=(get_first_date(project["start_date"]), get_first_date(project["end_date"])), step=timedelta(weeks=4))
        disabled_columns = get_disabled_columns(project)
        columns_order = get_column_order(filter_start, filter_end)
        
        #Filtered person information
        contract = contracts[contracts['person'] == person].iloc[0]     
        start_date = get_first_date(contract["start_date"])
        end_date = get_first_date(contract["end_date"])
        
        executed = get_first_date(project['executed'])

        sheet, activities, real_work, planned_work = fetch_data(project, person, start_date, end_date)
        
        st.subheader("Folha de Horas") ######### Folha de Horas
        modifications = st.data_editor(
            sheet.loc[['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', "Horas Reais"]].apply(pd.to_numeric, errors='coerce').fillna(0),
            key = get_dataframe_key("Hours", person),
            use_container_width=True,
            column_order=columns_order,
            disabled=disabled_columns,
            column_config=get_columns_config(start_date, end_date, 'Integer'),
        )

        modifications.loc['Horas Trabalhadas'] = modifications.loc['Jornada Diária'].fillna(0) * modifications.loc['Dias Úteis'].fillna(0) - modifications.loc['Faltas'].fillna(0) - modifications.loc['Férias'].fillna(0)
        modifications.loc['FTE'] = (modifications.loc['Horas Reais'].fillna(0) / (modifications.loc['Jornada Diária'].fillna(0) * modifications.loc['Dias Úteis'].fillna(0) - modifications.loc['Férias'].fillna(0)).replace(0, np.nan)).fillna(0)
        
        modifications_container = st.container()

        
        # st.dataframe(
        #     modifications.loc[['Horas Trabalhadas', 'FTE']].style.format("{:.2f}").map(format_zeros),
        #     use_container_width=True,
        #     column_order=columns_order,
        #     column_config=get_columns_config(start_date, end_date, 'Integer')
        # )
        modifications.loc['Salário'] = None
        modifications.loc['SS'] = None

        
        st.subheader("Folha Salarial") ######## Folha Salarial
        
        if st.toggle("Tabela Vertical"):
            
            salary_df = st.data_editor(
                get_salary_table(sheet.loc[["Salário", "SS"]]),
                key=get_dataframe_key("salary_vertical_table", person),
                column_config={
                    "Data":st.column_config.DateColumn("Data", format="MMM/YY", min_value= start_date if not executed else executed, max_value=end_date, required=True),
                    "Salário":st.column_config.NumberColumn("Salário", format="%.2f €", required=True),
                    "SS":st.column_config.NumberColumn("SS", format="%.2f", default=23.75,  required=True)
                },
                hide_index=True,
                use_container_width=True,
                num_rows='dynamic'
            )
            
            salary_df = salary_df.sort_values(by="Data")
            for row in salary_df.itertuples(index=False):
                date = get_first_date(row.Data)
                modifications.loc[["Salário", "SS"], date_range(date, end_date)] = {'Salário':row.Salário, 'SS':row.SS}

        else:

            modifications.loc[['Salário','SS']] = st.data_editor(
                sheet.loc[['Salário', 'SS']],
                use_container_width=True,
                column_order=columns_order,
                disabled=disabled_columns,
                key = get_dataframe_key("salario_column", person),
                column_config=get_columns_config(start_date, end_date, 'Float'),
            )
        
        modifications.loc['Custo Aproximado'] =  ( modifications.loc['Horas Reais'] / (modifications.loc['Jornada Diária'] * modifications.loc['Dias Úteis']).replace(0, np.nan) * modifications.loc['Salário']*14 / 11 * (1 + modifications.loc['SS'] / 100)).fillna(0)

        if save:  #Update Folha de Horas
            to_update = modifications.transpose()
            to_update = to_update.reset_index('date')
            to_update['date'] = pd.to_datetime(to_update['date'], format='%b/%y')
            to_update['person'] = person
            
            st.session_state.sheets = st.session_state.sheets.query('(person != @person) or (date < @start_date or date > @end_date)')
            st.session_state.sheets = pd.concat([st.session_state.sheets, to_update[['person', 'date', 'Jornada Diária', 'Faltas', 'Férias', 'Salário', 'SS', 'Custo Aproximado']]])
            
            to_update['day'] = to_update['Dias Úteis']
            to_update['hours'] = to_update['Horas Reais']
            to_update['project'] = project['name']
            st.session_state.real_work = st.session_state.real_work.query('(person != @person) or (project != @project["name"]) or (date < @start_date or date > @end_date)')
            st.session_state.real_work = pd.concat([st.session_state.real_work, to_update[['person', 'project', 'date', 'hours']]])
            st.session_state.working_days = st.session_state.working_days.query('project != @project["name"] or (date < @start_date or date > @end_date)')
            st.session_state.working_days = pd.concat([st.session_state.working_days, to_update[['project', 'date', 'day']]])

        st.dataframe(
            modifications.loc[['Custo Aproximado']].style.format("{:.2f} €").map(format_zeros),
            use_container_width=True,
            column_order=columns_order,
            column_config=get_columns_config(start_date, end_date, 'Integer')
        )

        st.subheader("Horas Planeadas") ### Horas Planeadas

        wp_sum_container = st.container()

        planned_work = planned_work.merge(activities[['activity', "wp", 'trl']], on="activity", how="left")
        planned_work = planned_work.drop(columns=['person', 'project'])
        planned_work = planned_work.sort_values(by="wp")

        wp_sheet = pd.DataFrame(columns=sheet.columns)

        for wp in planned_work['wp'].unique():

            wp_work = planned_work[planned_work['wp'] == wp]
            wp_work = wp_work.pivot(index="activity", columns="date", values="hours")
            wp_work.columns = wp_work.columns.strftime('%b/%y')

            wp_sheet_modifications = st.data_editor(
                wp_work.apply(pd.to_numeric, errors='coerce'),
                use_container_width=True,
                column_order=columns_order,
                disabled=disabled_columns,
                key = get_dataframe_key("work", person, wp),
                column_config=get_columns_config(start_date, end_date, 'Integer', "activity", wp),
            )
            
            wp_sheet = pd.concat([wp_sheet, wp_sheet_modifications])
        

        summary_wp = wp_sheet.reset_index(names="activity").merge(activities[["wp", "activity"]], how="left", on="activity")
        df_sum = summary_wp.groupby("wp").sum()
        df_sum.loc["Total"] =  summary_wp.sum()
        df_sum = df_sum.drop("activity", axis=1)
       
        wp_sum_container.dataframe(
            df_sum,
            use_container_width=True,
            column_order=columns_order,
            column_config=get_columns_config(start_date, end_date, 'Integer', 'wp', 'Tabela Resumo'),
        )

        st.subheader("Outros Projetos") ###### Outras Atividades Section
        
        other_projects = real_work.query('date >= @start_date and date <= @end_date and project != @project["name"]')[['date','hours', 'project']]
        other_projects['date'] = other_projects['date'].apply(lambda x: pd.to_datetime(x).strftime('%b/%y'))
        
        non_removable_projects = real_work.query('project in @st.session_state.projects["name"]')['project'].unique()
        removable_projects = real_work.query('project not in @st.session_state.projects["name"]')['project'].unique()
        projects_suggestion = st.session_state.real_work.query('project not in @st.session_state.projects["name"]')['project'].unique()
        
        project_list = st_tags(
            list(other_projects.query('project not in @st.session_state.projects["name"]')['project'].unique()),
            suggestions=projects_suggestion,
            label="Projetos não geridos",
            key=f"{person}_project_selector_{st.session_state.key}"
        )

        # editable_activities = other_activities.query('project not in  @st.session_state.projects["name"]').pivot_table(index='project', columns='date', values='hours')
        other_projects = other_projects.pivot_table(index='project', columns='date', values='hours')
        other_projects = pd.concat([pd.DataFrame(columns=sheet.columns), other_projects])


        for project_ in project_list:
            if project_ not in other_projects.index:
                other_projects.loc[project_] = None

        other_projects = other_projects.query('index in @project_list or index in @non_removable_projects')
        
        other_projects = st.data_editor(
            other_projects.apply(pd.to_numeric, errors='coerce'),
            use_container_width=True,
            column_order=columns_order,
            key=get_dataframe_key("other_project", person),
            column_config=get_columns_config(start_date, end_date, 'Integer', header="Projeto"),
        )

        remainder = pd.DataFrame(columns=sheet.columns)
        remainder.loc['Outras Atividades'] = modifications.loc['Horas Trabalhadas'] - other_projects.sum(axis=0) - modifications.loc['Horas Reais'].fillna(0)
        df_style = remainder.style.map(format_zeros)
        df_style = df_style.format("{:.0f}")
        df_style = df_style.apply(highlight_negative ,axis=1)


        modifications.loc["Horas Planeadas"] = summary_wp.sum()
        modifications.loc["Horas Restantes"] = modifications.loc['Horas Trabalhadas'] - other_projects.sum(axis=0) - modifications.loc['Horas Reais'].fillna(0)

        modifications_container.dataframe(
            modifications.loc[['Horas Trabalhadas', 'FTE', 'Horas Planeadas', "Horas Restantes"]].style.format("{:.2f}").map(format_zeros_and_negatives),
            use_container_width=True,
            column_order=columns_order,
            column_config=get_columns_config(start_date, end_date, 'Integer')
        )
        
        st.dataframe(
            df_style,
            use_container_width=True,
            column_order=columns_order,
            column_config=get_columns_config(start_date, end_date, 'Integer'),
        )   

        if save: #Real Work (other projects) update 
            other_projects = other_projects.reset_index(names="project")
            df = other_projects.melt(id_vars="project", var_name="date",  value_name="hours")
            df['date'] = pd.to_datetime(df['date'], format='%b/%y')
            df['person'] = person
            
            df = df.dropna(subset="hours")

            st.session_state.real_work.query('~ (person == @person and project != @project["name"] and date >= @start_date and date <= @end_date)', inplace=True)
            st.session_state.real_work = pd.concat([st.session_state.real_work, df])

        if not wp_sheet.empty:

            if save: # Planned work update
                wp_sheet = wp_sheet.reset_index(names='activity')
                wp_sheet = wp_sheet.melt(id_vars='activity', var_name='date', value_name='hours')
                wp_sheet['date'] = pd.to_datetime(wp_sheet['date'], format='%b/%y')
                wp_sheet['person'] = person
                wp_sheet['project'] = project['name']
                wp_sheet.replace(np.nan, 0, inplace=True)

                for act in st.session_state.activities.query('project == @project["name"]').itertuples(index=False):
                    wp_sheet = wp_sheet.query('not (activity == @act.activity and (date < @act.real_start_date or date > @act.real_end_date))')
                    
                st.session_state.planned_work = st.session_state.planned_work.query('(person != @person) or (project != @project["name"]) or (date < @start_date or date > @end_date)')
                st.session_state.planned_work = pd.concat([st.session_state.planned_work, wp_sheet])
                st.session_state.notification= {"message":"Atualizado", "type":"success"}
                reset_key()

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
                    },
                    use_container_width=True,
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
                    },
                    use_container_width=True
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
                column_order=columns_order,
                column_config={
                    "wp":st.column_config.TextColumn(
                        "WP",
                        width="small"
                    ),
                    "trl":st.column_config.TextColumn(
                        "TRL",
                        width="small"
                    ),
                },
                use_container_width=True,
            )
        
        sync_dataframes()
