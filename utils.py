from datetime import timedelta
import datetime
import calendar
import pandas as pd
import streamlit as st
import numpy as np
from itertools import product
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Color, PatternFill, Font, Border

def date_range(start, end):
    months_range = pd.date_range(start=get_first_date(start), end=get_last_date(end), freq='MS')
    return [month.strftime('%b/%y') for month in months_range]

def reset_key():
    st.session_state.key = (st.session_state.key + 1) % 2

def get_first_date(date):
    return datetime.date(date.year, date.month, 1)

def get_last_date(date):
    _, last_day = calendar.monthrange(date.year, date.month)
    return datetime.date(date.year, date.month, last_day)

def create_new_project(name, start, end):
    if not st.session_state.projects[st.session_state.projects['name'] == name].empty:
        return st.error("Projeto já existe")

    st.session_state.projects.loc[len(st.session_state.projects)] = [name, start, end, None]
    
    reset_key()
    st.rerun()

def add_project(name, start, end, activities, team, sheets, planned_work, real_work):
        
    if not st.session_state.projects[st.session_state.projects['name'] == name].empty:
        return st.error("Projeto já existe")

    st.session_state.projects.loc[len(st.session_state.projects)] = [name, start, end, None]
    
    st.session_state.activities = pd.concat([st.session_state.activities, activities])
    st.session_state.contracts = pd.concat([st.session_state.contracts , team])

    st.session_state.sheets = pd.concat([st.session_state.sheets , sheets])
    st.session_state.sheets = st.session_state.sheets.drop_duplicates(subset=["person","date"])
    st.session_state.real_work = pd.concat([st.session_state.real_work , real_work])
    st.session_state.real_work = st.session_state.real_work.drop_duplicates(subset=["person","project","date"])

    for act in activities.itertuples(index=False):
        planned_work = planned_work.query('~ (activity == @act.activity and (date < @act.real_start_date or date > @act.real_end_date))')

    st.session_state.planned_work = pd.concat([st.session_state.planned_work , planned_work])

    reset_key()
    st.rerun()
    

def update_project_dates(project, start, end):
    st.session_state.projects.loc[st.session_state.projects['name'] == project["name"], ["start_date", "end_date"]] = [start, end]

def update_timeline(project, data, executed, to_adjust):
    st.session_state.activities = st.session_state.activities.query('project != @project["name"]')
    st.session_state.activities = pd.concat([st.session_state.activities, data])
    executed = pd.to_datetime(executed)

    st.session_state.projects.query('name == @project["name"]').loc[0, 'executed'] = executed
    
    contracts = st.session_state.contracts.query('project == @project["name"]')
    if to_adjust:
        if not executed:
            sum_act = st.session_state.planned_work.query('project == @project["name"]').groupby(['person', 'activity'])['hours'].sum()
        else:
            sum_act = st.session_state.planned_work.query('project == @project["name"] and date > @executed').groupby(['person', 'activity'])['hours'].sum()
        

        for act in data.itertuples(index=False):
            act_range = pd.date_range(start= get_first_date(act.real_start_date), end= get_last_date(act.real_end_date), freq="MS")

            if not executed:
                st.session_state.planned_work = st.session_state.planned_work.query('~ (project == @project["name"] and activity == @act.activity)')
            else:
                st.session_state.planned_work = st.session_state.planned_work.query('~ (project == @project["name"] and activity == @act.activity and date > @executed)')


            comb = list(product(contracts['person'], act_range))
            act_df = pd.DataFrame({"person": [item[0] for item in comb], "project": project['name'], "activity": act.activity, "date": [item[1] for item in comb], "hours":0})
            st.session_state.planned_work = pd.concat([st.session_state.planned_work, act_df])
            

        st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "activity", "date"])
        st.session_state.planned_work = st.session_state.planned_work.sort_values(by="date")
    
    
        for contract in contracts.itertuples():
            
            contract_start_date = get_first_date(contract.start_date)
            contract_end_date = get_last_date(contract.end_date)

            st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract_start_date and date <= @contract_end_date)')
            
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
    else:
        for act in data.itertuples(index=False):
            real_start_date = get_first_date(act.real_start_date)
            real_end_date = get_last_date(act.real_end_date)
            act_range = pd.date_range(start= real_start_date, end= real_end_date, freq="MS")
            
            comb = list(product(contracts['person'], act_range))
            act_df = pd.DataFrame({"person": [item[0] for item in comb], "project": project['name'], "activity": act.activity, "date": [item[1] for item in comb], "hours":0})
            st.session_state.planned_work = st.session_state.planned_work.query('~ (activity == @act.activity and project == @project["name"] and (date < @real_start_date or date > @real_end_date))')
            st.session_state.planned_work = pd.concat([st.session_state.planned_work, act_df])
            
        st.session_state.planned_work = st.session_state.planned_work.dropna(subset=['hours'])
        st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "activity", "date"])
        st.session_state.planned_work = st.session_state.planned_work.sort_values(by="date")

        for contract in contracts.itertuples():        
            contract_start_date = get_first_date(contract.start_date)
            contract_end_date = get_last_date(contract.end_date)

            st.session_state.planned_work = st.session_state.planned_work.query('~ (person == @contract.person and (date < @contract_start_date or date > @contract_end_date))')
            

    st.rerun()
    
def update_contracts(project, data):
    st.session_state.contracts = st.session_state.contracts.query('project != @project["name"]')
    st.session_state.contracts = pd.concat([st.session_state.contracts, data])

    activities = st.session_state.activities.query('project == @project["name"]')
    
    for contract in data.itertuples():

        contract_start_date = get_first_date(contract.start_date)
        contract_end_date = get_last_date(contract.end_date)

        contract_range = pd.date_range(start= contract_start_date, end= contract_end_date, freq='MS')
        business_days = []
        for month_start in contract_range:
            business_days.append(len(pd.date_range(start=month_start, end=month_start + pd.offsets.MonthEnd(), freq=pd.offsets.BDay())))

        st.session_state.sheets = pd.concat([st.session_state.sheets, pd.DataFrame({"person": contract.person, "date": contract_range, "Jornada Diária": 8, "Dias Úteis":business_days, "Faltas": 0, "Férias": 0, "Salário": 0, "SS": 23.75})])

        st.session_state.real_work = st.session_state.real_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract_start_date and date <= @contract_end_date)')
        st.session_state.planned_work = st.session_state.planned_work.query('(person != @contract.person) or (project != @project["name"]) or (date >= @contract_start_date and date <= @contract_end_date)')

        st.session_state.real_work = pd.concat([st.session_state.real_work, pd.DataFrame({"person": contract.person, "project":project["name"], "date": contract_range, "hours":0})])
        
        for act in activities.itertuples(index=False):
            act_range = pd.date_range(start= get_first_date(act.real_start_date), end= get_last_date(act.real_end_date), freq='MS')
            st.session_state.planned_work = pd.concat([st.session_state.planned_work, pd.DataFrame({"person": contract.person, "project":project["name"], "activity":act.activity, "date":act_range, "hours":0})])

    st.session_state.sheets = st.session_state.sheets.drop_duplicates(subset=["person", "date"])
    st.session_state.real_work = st.session_state.real_work.drop_duplicates(subset=["person", "project", "date"])    
    st.session_state.real_work = st.session_state.real_work.query('(project != @project["name"]) or (person in @data["person"])')
    st.session_state.planned_work = st.session_state.planned_work.drop_duplicates(subset=["person", "project", "activity", "date"])
    st.session_state.planned_work = st.session_state.planned_work.query('(project != @project["name"]) or (person in @data["person"])')
 
    st.session_state.sheets = st.session_state.sheets.sort_values(by="date")
    st.session_state.planned_work = st.session_state.planned_work.sort_values(by="date")

def generate_sheets(project, start, end):
    
    wb = load_workbook('Sheet_Template.xlsx')
    template = wb['sheet']

    start = get_first_date(start)
    end = get_last_date(end)
    
    initial_diff = (start.year - project["start_date"].year) * 12 + start.month - project["start_date"].month
    
    for i in range(5, initial_diff + 5):
        template.column_dimensions[get_column_letter(i)].hidden = True
    
    x = initial_diff + 5
    for date in pd.date_range(start=start, end=end, freq="MS"):
        template.cell(row=4, column=x, value=date.strftime("%b/%y"))
        x += 1

    for i in range(x, 65):
        template.column_dimensions[get_column_letter(i)].hidden = True
        template.column_dimensions[get_column_letter(i)].width = 0

    for i in range(i, 200):
        template.column_dimensions[get_column_letter(i)].hidden

    contracts = st.session_state.contracts.query('project == @project["name"]')
    
    for contract in contracts.itertuples(index=False):
        sheet = wb.copy_worksheet(template)

        sheet.title= contract.person

        df = st.session_state.sheets.query('person == @contract.person and date >= @start and date <= @end')
        real_work = st.session_state.real_work.query('person == @contract.person and date >= @start and date <= @end')

        project_work = real_work.query('project == @project["name"]')
        other_work = real_work.query('project != @project["name"]')

        other_work = other_work.sort_values(by="project")

        row = 15
        for other_project in other_work['project'].unique():
            sheet.cell(row=row, column=4, value=other_project)
            row += 1
        
        for x in range(row, 21):
            sheet.row_dimensions[x].hidden = True

        planned_work = st.session_state.planned_work.query('person == @contract.person and project == @project["name"] and date >= @start and date <= @end')

        df_t = df.drop(columns='person').set_index('date')
        df_t = df_t.transpose()

        planned_work = planned_work.pivot(index="activity", columns="date", values="hours")
      
        horas_trabalhaveis = (df_t.loc['Jornada Diária'] * df_t.loc['Dias Úteis']).fillna(0)
        sum_wp = planned_work.sum()
        
        sum_wp= sum_wp.replace(0, np.nan)
        horas_trabalhaveis = horas_trabalhaveis.replace(0, np.nan)
        real_work = project_work.pivot(index="person", columns="date", values="hours")
    
        planned_work = ( (planned_work /sum_wp * real_work.loc[contract.person]).div(horas_trabalhaveis) ).fillna(0)
        planned_work = planned_work.reset_index(names="activity")

        planned_work = planned_work.merge(st.session_state.activities[['activity', "wp", 'trl']], on="activity", how="left")
        planned_work = planned_work.groupby(["wp", "trl"]).sum().drop(columns="activity")

        planned_work.columns = planned_work.columns.map(lambda col: col.strftime("%b/%y"))
        #print(planned_work)
        row = 23
        for wp in planned_work.index.get_level_values(0).unique():
            sheet.cell(row=row, column=3, value=wp)
            row += 2

        for row in range(row, 43):
            sheet.row_dimensions[row].hidden = True

        x = initial_diff + 5
        for date in pd.date_range(start=start, end=end, freq="MS"):
            if not (row := df.loc[df['date'] == date]).empty:
                sheet.cell(row=5, column=x, value= row['Jornada Diária'].iloc[0])
                sheet.cell(row=6, column=x, value= row['Dias Úteis'].iloc[0])
                sheet.cell(row=8, column=x, value= val if (val:= row['Faltas'].iloc[0]) != 0 else "")
                sheet.cell(row=9, column=x, value= val if (val:= row['Férias'].iloc[0]) != 0 else "")

            if not (val:= project_work.loc[project_work['date'] == date, 'hours']).empty:
                sheet.cell(row=14, column=x, value= val.iloc[0])

            row = 15
            for res in other_work.loc[other_work['date'] == date].itertuples(index=False):
                sheet.cell(row=row, column=x, value= res.hours)
                row += 1
            
            row = 23
            while (wp:= sheet.cell(row= row, column=3).value):
                try:
                    sheet.cell(row=row, column=x, value=planned_work.loc[(wp, 'TRL 3-4'), date.strftime("%b/%y")])
                except:
                    pass 
                try:
                    sheet.cell(row=row+1, column=x, value=planned_work.loc[(wp, 'TRL 5-9'), date.strftime("%b/%y")])
                except:
                    pass

                row += 2

            x += 1
            
        
        sheet.sheet_view.showGridLines = False

        blueFill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
        blueFont = Font(color="0070C0", name="Aptos Narrow", bold=True)
        sheet.conditional_formatting.add('E23:BL42', CellIsRule('greaterThan', formula=['0'], fill=blueFill, font=blueFont))

    del wb["sheet"]

    return wb

def generate_pay_sheets(project, file, start, end, df_team, df_trl):
    start = get_first_date(start)
    end = get_last_date(end)

    sheets = st.session_state.sheets.query('person in @df_team["equipa"].unique() and date >= @start and date <= @end')
    project_work = st.session_state.real_work.query('project == @project["name"] and date >= @start and date <= @end')
    project_work = project_work.rename(columns={'hours':'real_work'})
    planned_work = st.session_state.planned_work.query('project == @project["name"] and date >= @start and date <= @end')

    sheets['horas_trabalhaveis'] = sheets['Jornada Diária'] * sheets['Dias Úteis']
    
    planned_work = planned_work.merge(st.session_state.activities[['wp', 'trl', 'activity']], on="activity", how="left")
    sum_wp = planned_work.groupby(["wp","person"])['hours'].sum().reset_index()
    sum_wp = sum_wp.rename(columns={'hours':'wp_sum'})    

    planned_work = planned_work.merge(project_work[["person", "date", "real_work"]], on=["person", "date"], how="left")
    planned_work = planned_work.merge(sum_wp[["wp", "person", "wp_sum"]], on=["person", "wp"], how="left")
    planned_work = planned_work.merge(sheets[["date", "person", "horas_trabalhaveis"]], on=["person", "date"], how="left")

    planned_work['res'] = ((planned_work['hours'] / planned_work['wp_sum'] * planned_work['real_work']) / planned_work['horas_trabalhaveis']).fillna(0)
    df_team = df_team.merge(planned_work[["person", "wp", "trl", "date", "res"]], left_on="equipa", right_on="person")
    df_team = df_team.groupby(["tecnico", "wp", "trl", "date"])["res"].sum().reset_index()
    df_team = df_team[df_team['res'] > 0]

    df_team = df_team.merge(df_trl, on=["wp", "trl"], how="left")
    df_team = df_team[~ pd.isna(df_team['investimento'])]
    
    wb = load_workbook(file)
    ws = wb['Mapa']

    for i, val in enumerate(df_team.itertuples(index=False), start=4):

        ws[f'C{i}'] = val.investimento
        ws[f'D{i}'] = val.tecnico
        ws[f'E{i}'] = '{}/{}'.format(val.date.month, val.date.year)
        ws[f'G{i}'] = val.res
    
    return wb

@st.cache_data
def read_timesheet(file, project):

    team = pd.read_excel(file, sheet_name="Equipa de projeto", usecols="C:G", header=7, names=["profile", "person", "gender", "start_date", "end_date"]).dropna(subset="person")
    team = pd.concat([team, pd.read_excel(file, sheet_name="Equipa de projeto", usecols=[2,7,8,9,10], header=7, names=["profile", "person", "gender", "start_date", "end_date"]).dropna(subset="person")])
   
    timeline = pd.read_excel(file, sheet_name="Cronograma", usecols=[1, 5], header=8, names=["activity","trl"])
    timeline['line'] = timeline.index + 10
    timeline = timeline.dropna(subset="activity").fillna(method='bfill')
    
    df_colors, start_date, end_date = extract_cell_colors_and_dates(file)

    start_date = get_first_date(start_date)
    end_date = get_last_date(end_date)

    team.loc[pd.isna(team['end_date']), "end_date"] = end_date

    activities = pd.DataFrame()

    wp_index = [ind for ind in timeline.index if (ind % 131) == 0]

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
    activities[['start_date', 'end_date']] = activities.apply(lambda row: min_max_dates(row, -1, 1), axis=1, result_type='expand')
    activities[['real_start_date', 'real_end_date']] = activities.apply(lambda row: min_max_dates(row, 2, 1), axis=1, result_type='expand')
   
    activities.loc[pd.isna(activities['start_date']), "start_date"] = start_date
    activities.loc[pd.isna(activities['end_date']), "end_date"] = end_date
    activities.loc[pd.isna(activities['real_start_date']), "real_start_date"] = start_date
    activities.loc[pd.isna(activities['real_end_date']), "real_end_date"] = end_date

    activities['project'] = project
    activities["trl"] = "TRL " + activities['trl']
        
    activities = activities[['activity', 'trl','wp','start_date','end_date','real_start_date','real_end_date', 'project']]
    team['project'] = project
    
    cols_to_convert = ['start_date','end_date','real_start_date','real_end_date']
    activities[cols_to_convert] = activities[cols_to_convert].apply(pd.to_datetime)

    sheets = pd.DataFrame()
    planned_works = pd.DataFrame()
    real_works = pd.DataFrame()
    
    for contract in team.itertuples():
        sheet = f'{contract.Index + 1}. {contract.person}'

        df = pd.read_excel(file, sheet_name=sheet, header=3).iloc[:,3:]
    
        df = df.rename(columns={df.columns[0]: 'date'})
        df = df.set_index("date")
        
        contract_range = pd.date_range(start= get_first_date(contract.start_date), end= contract.end_date, freq="MS")
        sheet = df.loc[['Jornada diária', 'N.º de dias \núteis','Faltas (horas/mês)','Férias (horas/mês)','Salário atualizado (€)','SS'], contract_range].fillna(0)
        sheet = sheet.transpose().reset_index(names="date")

        sheet = sheet.rename(columns={
            "Jornada diária":"Jornada Diária",
            "N.º de dias \núteis":"Dias Úteis",
            "Faltas (horas/mês)":"Faltas",
            "Férias (horas/mês)":"Férias",
            "Salário atualizado (€)":"Salário"
        })

        sheet["SS"] = sheet["SS"] * 100
        sheet["person"] = contract.person
        sheet["date"] = pd.to_datetime(sheet['date'])

        sheets = pd.concat([sheets, sheet])

        planned_work = df.loc[activities['activity'].unique(), contract_range]
        planned_work = planned_work[~planned_work.index.duplicated()].fillna(0)

        planned_work = planned_work.reset_index(names="activity").melt(id_vars='activity', var_name='date', value_name='hours')
        planned_work['project'] = project
        planned_work['person'] = contract.person
        planned_work["date"] = pd.to_datetime(planned_work['date'])

        planned_works = pd.concat([planned_works, planned_work])

        real_work = df.loc[['Horas Reais PRR'], contract_range]

        index_position = df.index.get_loc('Outras atividades')
        other_activities = df.iloc[index_position-3:index_position].loc[:, contract_range]
        other_activities= other_activities[other_activities.index.notna()]

        real_work = pd.concat([real_work, other_activities]).fillna(0)
        real_work = real_work.reset_index(names="project").melt(id_vars='project', var_name='date', value_name='hours')

        real_work['person'] = contract.person
        real_work['date'] = pd.to_datetime(real_work['date'])

        real_work.loc[real_work['project'] == 'Horas Reais PRR', "project"] = project

        real_works = pd.concat([real_works, real_work])

        team['person'] = team['person'].str.title()
        sheets['person'] = sheets['person'].str.title()
        real_works['person'] = real_works['person'].str.title()
        planned_works['person'] = planned_works['person'].str.title()
    
    return team, activities, sheets, planned_works, real_works, start_date, end_date

def extract_cell_colors_and_dates(file):
    # Load the Excel workbook
    wb = load_workbook(file, data_only=True)
    ws = wb['Cronograma']

    months = pd.read_excel(file, sheet_name="Cronograma", header=8, nrows=0).iloc[:, 6:]

    # Initialize an empty list to store cell colors
    colors_data = []

    # Iterate through each row and column in the worksheet

    for row in ws.iter_rows():
        row_colors = []
        for cell in row:
            # Get the fill color of the cell
            fill = cell.fill.start_color.index
            row_colors.append(fill)
        colors_data.append(row_colors)

    # Convert the list of colors into a DataFrame
    df = pd.DataFrame(colors_data)
    df = df.iloc[:, 6: 6+len(months.columns)] 

    active_color = ws['G1325'].fill.start_color.index
    deactivated_color = ws['O1326'].fill.start_color.index
    print(deactivated_color)
    extended_color = ws['G1326'].fill.start_color.index

    df = df.replace(active_color, 1)
    df = df.replace(deactivated_color, -1)
    df = df.replace(extended_color, 2)
    
    df.columns = months.columns

    return df, months.columns[0], months.columns[-1]

def min_max_dates(row, value1, value2):
    dates = []
    for col, val in row.items():
        if val in [value1, value2]:
            dates.append(col)
    if len(dates) == 0:
        return None, None
    return min(dates), max(dates)