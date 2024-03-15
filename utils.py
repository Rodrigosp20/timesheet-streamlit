import datetime, calendar, pickle, base64, pandas as pd, streamlit as st
from openpyxl import load_workbook
import streamlit.components.v1 as components

# Data Schema 
projects_schema = {
    "name": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
    "executed": "datetime64[ns]"
}

activities_schema = {
    "project": "string",
    "wp": "string",
    "activity": "string",
    "trl": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
    "real_start_date": "datetime64[ns]",
    "real_end_date": "datetime64[ns]"
}

contracts_schema = {
    "project":"string",
    "person":"string",
    "profile":"string",
    "gender": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
}

sheets_schema = {
    "person" : "string",
    "date" : "datetime64[ns]",
    "Jornada Diária" : "int64",
    "Dias Úteis": "int64",
    "Faltas" : "float64",
    "Férias" : "float64",
    "Salário" : "float64",
    "SS" : "float64",
    "Custo Aproximado" : "float64",
}

real_work_schema = {
    "person" : "string",
    "project" : "string",
    "date" : "datetime64[ns]",
    "hours" : "int64"
}

planned_work_schema = {
    "person" : "string",
    "project": "string",
    "activity" : "string",
    "date" : "datetime64[ns]",
    "hours" : "int64"
}

def create_session():
    """ Initialize streamlit session variables """
    
    if 'key' not in st.session_state:
        st.session_state.key = 0
    
    if 'activities' not in st.session_state:
        st.session_state.activities = pd.DataFrame(columns=activities_schema.keys()).astype(activities_schema)
        st.session_state.contracts = pd.DataFrame(columns=contracts_schema.keys()).astype(contracts_schema)
        st.session_state.projects = pd.DataFrame(columns=projects_schema.keys()).astype(projects_schema)
        st.session_state.sheets = pd.DataFrame(columns=sheets_schema.keys()).astype(sheets_schema)
        st.session_state.planned_work = pd.DataFrame(columns=planned_work_schema.keys()).astype(planned_work_schema)
        st.session_state.real_work = pd.DataFrame(columns=real_work_schema.keys()).astype(real_work_schema)

def save_data():
    """ Download all data """

    object_to_download = pickle.dumps({
        'activities':st.session_state.activities,
        'contracts':st.session_state.contracts,
        'projects':st.session_state.projects,
        'sheets': st.session_state.sheets,
        'planned_work' : st.session_state.planned_work,
        'real_work' : st.session_state.real_work
    })

    b64 = base64.b64encode(object_to_download).decode()
    download_filename = "data.pkl"

    components.html(
        f"""
            <html>
                <head>
                <title>Start Auto Download file</title>
                <a id="fileDownload" href="data:application/octet-stream;base64,{b64}" download="{download_filename}">
                <script>
                    document.getElementById('fileDownload').click();
                </script>
                </head>
            </html>
        """,
        height=0,
    )

def invalid(*args):
    """ Check if variables aren't empty """
    
    for arg in args:
        if arg is None:
            return True
        
        if type(arg) == str and len(arg) == 0:
            return True
    
    return False

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