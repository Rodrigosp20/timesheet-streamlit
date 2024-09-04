import streamlit as st
from datetime import timedelta
import pandas as pd
import numpy as np
from utils import activities_schema, get_topbar, set_notification, working_days_schema, contracts_schema, sheets_schema, planned_work_schema, real_work_schema
from utils import min_max_dates
from utils import extract_cell_colors_and_dates, get_first_date, get_last_date, invalid

def create_new_project(name, start, end):
    """ Creates new empty project """
    if not st.session_state.projects[st.session_state.projects['name'] == name].empty:
        return set_notification("error", "Projeto já existe")
    
    if name in ['Projetos', 'Adicionar Projeto', 'Funcionários']:
        return set_notification("error", "Nome de projeto inválido")
    
    if start >= end:
        return set_notification("error", "Datas inválidas")

    st.session_state.projects.loc[len(st.session_state.projects)] = [name, start, end, None]

    project_range = pd.date_range(start= get_first_date(start), end= end, freq='MS')
    business_days = []
    for month_start in project_range:
        business_days.append(len(pd.date_range(start=month_start, end=month_start + pd.offsets.MonthEnd(), freq=pd.offsets.BDay())))
    
    st.session_state.working_days = pd.concat([st.session_state.working_days, pd.DataFrame({"project": name, "day":business_days, "date":project_range})])
    st.session_state.working_days = st.session_state.working_days.drop_duplicates(subset=["project","date"])
    
    set_notification("success", "Projeto criado com sucesso", force_reset=True)

def check_columns(df, columns):
    if set(columns).issubset(df.columns):
        return df[columns]
    raise Exception("Wrong Dataframe Format")

def add_project(name, start, end, activities, team, sheets, planned_work, real_work, working_days):
    """ add existing project """

    if not st.session_state.projects[st.session_state.projects['name'] == name].empty:
        return st.error("Projeto já existe")
    
    if ((activities['start_date'] >= activities['end_date']) | (activities['real_start_date'] >= activities['real_end_date'])).any():
        return st.error("Atividades com datas inválidas")

    activities['project'] = name
    team['project'] = name
    planned_work['project'] = name
    working_days['project'] = name
    real_work.loc[real_work['project'] == 'Horas Reais PRR', 'project'] = name

    activities = check_columns(activities, activities_schema.keys())
    team = check_columns(team, contracts_schema.keys())
    planned_work = check_columns(planned_work, planned_work_schema.keys())
    real_work = check_columns(real_work, real_work_schema.keys())
    sheets = check_columns(sheets, sheets_schema.keys())
    working_days = check_columns(working_days, working_days_schema.keys())
    
    st.session_state.projects.loc[len(st.session_state.projects)] = [name, start, end, None]

    st.session_state.activities = pd.concat([st.session_state.activities, activities])
    st.session_state.contracts = pd.concat([st.session_state.contracts , team])

    st.session_state.sheets = pd.concat([st.session_state.sheets , sheets])
    st.session_state.sheets = st.session_state.sheets.drop_duplicates(subset=["person","date"])
    st.session_state.real_work = pd.concat([st.session_state.real_work , real_work])
    st.session_state.real_work = st.session_state.real_work.drop_duplicates(subset=["person","project","date"])
    st.session_state.working_days = pd.concat([st.session_state.working_days, working_days])
    st.session_state.working_days = st.session_state.working_days.drop_duplicates(subset=["project","date"])
    for act in activities.itertuples(index=False):
        planned_work = planned_work.query('~ (activity == @act.activity and (date < @act.real_start_date or date > @act.real_end_date))')

    st.session_state.planned_work = pd.concat([st.session_state.planned_work , planned_work])

    team = team[["person", "gender"]].rename({'person':'name'}, axis='columns')
    st.session_state.persons = pd.concat([st.session_state.persons, team])
    st.session_state.persons.drop_duplicates(subset="name", inplace=True)

    set_notification("success", "Projeto criado com sucesso", force_reset=True)

@st.cache_data
def read_timesheet(file):
    """ Read timesheet from excel """

    try:
        team = pd.read_excel(file, sheet_name="Equipa de projeto", usecols="C:G", header=7, names=["profile", "person", "gender", "start_date", "end_date"]).dropna(subset="person")
        team = pd.concat([team, pd.read_excel(file, sheet_name="Equipa de projeto", usecols=[2,7,8,9,10], header=7, names=["profile", "person", "gender", "start_date", "end_date"]).dropna(subset="person")])
    except:
        raise Exception("Erro a ler a equipa de projeto")
    
    try:
        timeline = pd.read_excel(file, sheet_name="Cronograma", usecols=[1, 5], header=8, names=["activity","trl"])
    except:
        raise Exception("Erro a ler o cronograma")
    
    timeline['line'] = timeline.index + 10
    timeline = timeline.dropna(subset="activity").fillna(method='bfill')
    
    try:
        df_colors, start_date, end_date = extract_cell_colors_and_dates(file)  
    except:
        raise Exception("Erro a ler o cronograma")

    try:
        start_date = get_first_date(start_date)
        end_date = get_last_date(end_date)
    except:
        raise Exception("Datas inválidas no cronograma")

    team.loc[pd.isna(team['end_date']), "end_date"] = end_date  

    activities = pd.DataFrame()

    wp_index = [ind for ind in timeline.index if (ind % 131) == 0]

    # read activities data, trl and wp
    for i in range(len(wp_index)):
        wp = wp_index[i]

        if i+1 == len(wp_index):
            wp_next = np.Infinity
        else:
            wp_next = wp_index[i+1]
        
        wp_name = timeline.loc[wp, "activity"]

        wp_activities = timeline.loc[[ind for ind in timeline.index if (ind > wp and ind < wp_next and (ind-wp-1) % 13 == 0)], ["activity","trl", "line"]]
        wp_activities['wp'] = wp_name

        activities = pd.concat([activities, wp_activities])

    activities = pd.merge(activities, df_colors, left_on='line', right_index=True)
    try:
        activities[['start_date', 'end_date']] = activities.apply(lambda row: min_max_dates(row, -1, 1), axis=1, result_type='expand')
        activities[['real_start_date', 'real_end_date']] = activities.apply(lambda row: min_max_dates(row, 2, 1), axis=1, result_type='expand')
    except:
        raise Exception("Erro a ler as datas das atividades")
    
    activities.loc[pd.isna(activities['start_date']), "start_date"] = start_date
    activities.loc[pd.isna(activities['end_date']), "end_date"] = end_date
    activities.loc[pd.isna(activities['real_start_date']), "real_start_date"] = start_date
    activities.loc[pd.isna(activities['real_end_date']), "real_end_date"] = end_date

    try:
        activities["trl"] = "TRL " + activities['trl']
    except:
        pass

    activities = activities[['activity', 'trl','wp','start_date','end_date','real_start_date','real_end_date']]

    #Check if ther aren't any duplicated activities names
    assert not activities['activity'].duplicated().any() , "Existem atividades com nomes repetidos no ficheiro"
       
    cols_to_convert = ['start_date','end_date','real_start_date','real_end_date']
    activities[cols_to_convert] = activities[cols_to_convert].apply(pd.to_datetime)

    sheets = pd.DataFrame()
    planned_works = pd.DataFrame()
    real_works = pd.DataFrame()
    
    first_sheet = True
    #read person sheeets
    for contract in team.itertuples():
        sheet_name = f'{contract.Index + 1}. {contract.person}'

        try:
            df = pd.read_excel(file, sheet_name=sheet_name, header=3).iloc[:,3:]
        except:
            raise Exception(f"Não foi encontrada a folha {sheet_name}")
        
        df = df.rename(columns={df.columns[0]: 'date'})
        df = df.set_index("date")
        
        contract_range = pd.date_range(start= get_first_date(contract.start_date), end= contract.end_date, freq="MS")
        
        try:
            sheet = df.loc[['Jornada diária', 'N.º de dias \núteis','Faltas (horas/mês)','Férias (horas/mês)','Salário atualizado (€)','SS'], contract_range].fillna(0)
        except:
            raise Exception(f"Folha {sheet_name}: Erro na leitura da folha de horas")
        
        sheet = sheet.transpose().reset_index(names="date")
        
        sheet = sheet.rename(columns={
            "Jornada diária":"Jornada Diária",
            "N.º de dias \núteis":"day",
            "Faltas (horas/mês)":"Faltas",
            "Férias (horas/mês)":"Férias",
            "Salário atualizado (€)":"Salário"
        })
        
        try:
            sheet[['Jornada Diária', 'day', 'Faltas', 'Férias', 'Salário']] = sheet[['Jornada Diária', 'day', 'Faltas', 'Férias', 'Salário']].astype('float64')
        except:
            raise Exception(f"Erro a ler a folha {sheet_name} - Não foi possível converter a folha com Números Inválidos")
        
        sheet["SS"] = sheet["SS"] * 100
        sheet["person"] = contract.person
        sheet["date"] = pd.to_datetime(sheet['date'])

        if first_sheet:
            working_days = sheet[["date", "day"]]
            first_sheet = False
        
        sheets = pd.concat([sheets, sheet])
        
        try:
            planned_work = df.loc[activities['activity'].unique(), contract_range]
        except:
            raise Exception(f"Folha {sheet_name}: Não foram encontradas as atividades")
        
        planned_work = planned_work[~planned_work.index.duplicated()].fillna(0)

        planned_work = planned_work.reset_index(names="activity").melt(id_vars='activity', var_name='date', value_name='hours')
        planned_work['person'] = contract.person
        
        try:
            planned_work["date"] = pd.to_datetime(planned_work['date']) 
        except:
            raise Exception(f"Folha {sheet_name}: Erro a converter datas da folha")

        planned_works = pd.concat([planned_works, planned_work])
        
        try:
            real_work = df.loc[['Horas Reais PRR'], contract_range]
        except:
            raise Exception(f"Folha {sheet_name}: Não foi encontrado as Horas Reais [Horas Reais PRR]")

        try:
            index_position = df.index.get_loc('Outras atividades')
            other_activities = df.iloc[index_position-3:index_position].loc[:, contract_range]
            other_activities= other_activities[other_activities.index.notna()]
        except:
            raise Exception(f"Folha {sheet_name}: Erro a ler outras atividades")

        real_work = pd.concat([real_work, other_activities]).fillna(0)
        real_work = real_work.reset_index(names="project").melt(id_vars='project', var_name='date', value_name='hours')

        real_work['person'] = contract.person
        real_work['date'] = pd.to_datetime(real_work['date'])

        real_works = pd.concat([real_works, real_work])

        team['person'] = team['person'].str.title()
        sheets['person'] = sheets['person'].str.title()
        real_works['person'] = real_works['person'].str.title()
        planned_works['person'] = planned_works['person'].str.title()
    
    return team, activities, sheets, planned_works,   real_works, start_date, end_date, working_days

def home_widget():

    get_topbar("Adicionar Projeto", buttons=False)

    with_file = st.checkbox("Criar através de timesheet?")

    project_name = st.text_input("Nome do projeto", key=f"project_name_{st.session_state.key}")

    if not with_file:
        c1, c2 = st.columns(2)
        
        start_date = c1.date_input("Data de inicio", key=f"start_date_project_{st.session_state.key}", format="DD/MM/YYYY", value=None)
        end_date = c2.date_input("Data de encerramento", key=f"end_date_project_{st.session_state.key}", format="DD/MM/YYYY", value=None, min_value= start_date + timedelta(days=1, weeks=4) if start_date else None)
        
        if st.button("Criar Projeto", disabled= invalid(project_name, start_date, end_date), use_container_width=True):
            create_new_project(project_name, start_date, end_date)

        return
    
    if file := st.file_uploader("Timesheet", accept_multiple_files=False, type="xlsx", key=f"file_uploader_{st.session_state.key}"):
        
        try:
            team, activities, sheets, planned_work, real_work, start_date, end_date, working_days = read_timesheet(file) 
        except Exception as e:
            return set_notification("error", str(e))

       
        st.header("Equipa do Projeto")

        st.dataframe(
            team,
            column_config={
                "profile":st.column_config.TextColumn("Perfil"),
                "person":st.column_config.TextColumn("Pessoa"),
                "gender":st.column_config.TextColumn("Género"),
                "start_date":st.column_config.DateColumn("Data de Inicio", format="DD/MM/YYYY"),
                "end_date":st.column_config.DateColumn("Data de Conclusão", format="DD/MM/YYYY"),
            },
            hide_index=True,
            use_container_width=True
        )

        st.header("Atividades do Projeto")

        activities = st.data_editor(
            activities,
            column_order=("wp", "activity", "trl","start_date","end_date","real_start_date","real_end_date", "project"),
            column_config={
                "wp":st.column_config.TextColumn("WP",disabled=True),
                "activity": st.column_config.TextColumn(
                    "Atividade",
                    required=True,
                    width="medium",
                ),
                "trl": st.column_config.SelectboxColumn(
                    "TRL",
                    options=['TRL 3-4', 'TRL 5-9'],
                    required=True
                ),
                "start_date": st.column_config.DateColumn(
                    "Data de Inicio [Planeada]",
                    min_value=start_date,
                    format="DD/MM/YYYY",
                    required=True
                ),
                "end_date": st.column_config.DateColumn(
                    "Data de Conclusão [Planeada]",
                    max_value=end_date,
                    default=end_date,
                    format="DD/MM/YYYY",
                    required=True
                ),
                "real_start_date": st.column_config.DateColumn(
                    "Data de Inicio [Real]",
                    min_value=start_date,
                    max_value=end_date,
                    format="DD/MM/YYYY",
                    required=True
                ),
                "real_end_date": st.column_config.DateColumn(
                    "Data de Conclusão [Real]",
                    min_value=start_date,
                    max_value=end_date,
                    format="DD/MM/YYYY",
                    required=True
                )
            },
            use_container_width=True,
            hide_index=True
        )

        
    if st.button("Adicionar Projeto", disabled= invalid(project_name, file), use_container_width=True):
        add_project(project_name, start_date, end_date, activities, team, sheets, planned_work, real_work, working_days)
            
    