from datetime import timedelta
import datetime
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_tags import st_tags
from utils import *
from dateutil.relativedelta import relativedelta
from components import project_page, sidebar, home, timeline, team, sheet_page, time_allocation, cost_allocation


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
