import streamlit as st
from utils import *
from io import BytesIO
import numpy as np
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font
from openpyxl.formatting.rule import CellIsRule

def update_project_dates(project, start, end):
    st.session_state.projects.loc[st.session_state.projects['name'] == project["name"], ["start_date", "end_date"]] = [start, end]

def save_excel(file, name):
    b64 = base64.b64encode(file).decode()

    components.html(
        f"""
            <html>
                <head>
                <title>Start Auto Download file</title>
                <a id="fileDownload" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{name}">
                <script>
                    document.getElementById('fileDownload').click()
                </script>
                </head>
            </html>
        """,
        height=0,
    )

def generate_sheets(project, start, end):
    
    wb = load_workbook('assets/Sheet_Template.xlsx')
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

def project_widget(project):
    
    st.title(project['name'])

    with st.container(border=True):
            
        start_date = st.date_input("Data de Inicio", key=f"project_date_initial_{st.session_state.key}", value=project['start_date'], format="DD/MM/YYYY", max_value=project['start_date'])
        end_date = st.date_input("Data de Termino", key=f"project_date_final_{st.session_state.key}", value=project['end_date'], format="DD/MM/YYYY", min_value=project['end_date'])

        _,col2 = st.columns([0.55,0.45])
        col1, col2 = col2.columns(2)

        if col1.button("Guardar Alterações", key="save_project_dates", disabled=invalid(start_date, end_date)):
            update_project_dates(project, start_date, end_date)

        if col2.button("Descartar Alterações", key="discard_project_dates", on_click=reset_key):
            st.rerun()

    with st.expander("Gerar Folhas de Afetação"):
        start_date, end_date = st.slider(
            "Selecionar espaço temporal",
            min_value= project["start_date"],
            max_value= project["end_date"],
            value= (project["start_date"], project["end_date"]),
            format="MM/YYYY"
        )
        
        if st.button("Gerar Excel", use_container_width=True):
            wb = generate_sheets(project, start_date, end_date)
        
            virtual_workbook = BytesIO()
            wb.save(virtual_workbook)
            virtual_workbook.seek(0)
            
            save_excel(virtual_workbook.getvalue(), f"{project['name']}.xlsx")
    
    with st.expander("Gerar Folhas de Pagamentos"):
        start_date, end_date = st.slider(
            "Selecionar espaço temporal",
            min_value= project["start_date"],
            max_value= project["end_date"],
            value= (project["start_date"], project["end_date"]),
            format="MM/YYYY",
            key="slider_pay"
        )

        if template := st.file_uploader("Template", type=".xlsx", accept_multiple_files=False):
            df_team = pd.read_excel(template ,sheet_name="Referências", usecols="H", header=3, names=["tecnico"]).dropna()
            df_team['equipa'] = None

            df_team = st.data_editor(
                df_team,
                column_config={
                    "equipa":st.column_config.SelectboxColumn(
                        "equipa",
                        options=st.session_state.contracts.query('project == @project["name"]')["person"].unique()
                    )
                },
                disabled=["tecnico"],
                use_container_width=True,
                hide_index=True
            )

            df_trl = pd.read_excel(template, sheet_name="Referências", usecols="E", header=3, names=["investimento"]).dropna()
            df_trl['wp'] = None
            df_trl['trl'] = None

            df_trl = st.data_editor(
                df_trl,
                column_config={
                    "wp":st.column_config.SelectboxColumn(
                        "wp",
                        options=st.session_state.activities.query('project == @project["name"]')['wp'].unique()
                    ),
                    "trl":st.column_config.SelectboxColumn(
                        "trl",
                        options=st.session_state.activities.query('project == @project["name"]')['trl'].unique()
                    ),
                },
                disabled=['investimento'],
                hide_index=True,
                use_container_width=True
            )                    

        if st.button("Gerar Excel", key="pay_excel", use_container_width=True , disabled=False if template else True):
            wb = generate_pay_sheets(project, template, start_date, end_date, df_team, df_trl)

            virtual_workbook = BytesIO()
            wb.save(virtual_workbook)
            virtual_workbook.seek(0)

            save_excel(virtual_workbook.getvalue(), f"fpp_{project['name']}.xlsx")