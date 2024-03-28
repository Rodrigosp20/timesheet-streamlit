from components import project_page, sidebar, home, timeline, team, sheet_page, time_allocation, cost_allocation
import streamlit as st
from utils import create_session

st.set_page_config(
    page_title="My Streamlit App",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",  # 'centered' or 'wide'
    initial_sidebar_state="expanded",  # 'auto', 'expanded', 'collapsed'
)

def main():
    
    create_session()
    
    project = sidebar.sidebar_widget()
    
    if not project:
        return home.home_widget()
    
    tab = st.radio('', ['Projeto', 'Cronograma', 'Equipa', 'Pessoal', 'Imputação Horas', 'Custos'], index=0, horizontal=True)
    project = st.session_state.projects.query('name == @project').iloc[0]
    match tab:

        case 'Projeto':

            project_page.project_widget(project)

        case 'Cronograma':            
        
            timeline.timeline_widget(project)
    
        case 'Equipa':
    
            team.team_widget(project)

        case 'Pessoal':
        
            sheet_page.sheet_widget(project)

        case 'Imputação Horas':
        
            time_allocation.time_allocation_widget(project)
        
        case 'Custos':

            cost_allocation.cost_allocation_widget(project)
            
       
    
if __name__ == "__main__":
    main()
