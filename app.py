from components import project_page, sidebar, home, timeline, team, sheet_page, time_allocation, cost_allocation, workers
import streamlit as st
from utils import check_notification, create_session, fade_notification, reset_key, warning_before_leave
from streamlit_option_menu import option_menu
import streamlit_antd_components as sac
from utils import selected_operation
from streamlit_shortcuts import add_keyboard_shortcuts

st.set_page_config(
    page_title="Timesheet",
    page_icon=":newspaper:",
    layout="wide",  # 'centered' or 'wide'
    initial_sidebar_state="expanded",  # 'auto', 'expanded', 'collapsed'
)


def main():
    st.markdown("""
    <style>
        div[data-testid='column'] h2 {
            text-align:center;
        }
        
        section[class*="main"] > div > div > div > div > div[data-testid="element-container"]:last-of-type {
            position: fixed;            /* Stick to the viewport */
            bottom: 30px;              /* Space from the bottom */
            right: 80px;               /* Space from the right */
            background-color: rgba(50, 50, 50, 0.9); /* Dark background with slight transparency */
            border: 1px solid rgba(200, 200, 200, 0.5); /* Light border with transparency */
            border-radius: 5px;        /* Rounded corners */
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.7); /* Shadow for depth */
            max-width: 650px;          /* Max width to control size */
            z-index: 1000;             /* Ensure it's on top */
            font-family: Arial, sans-serif; /* Use a clean font */
            display: none;             /* Initially hidden */
            padding: 10px;             /* Padding inside the container */
            overflow: hidden;          /* Prevent overflow */
            white-space: nowrap;       /* Prevent line breaks */
        }

    </style>
    """, unsafe_allow_html=True)

    create_session()

    check_notification()

    page = sidebar.sidebar_widget()

    match page:

        case 'Adicionar Projeto':
            home.home_widget()

        case 'Funcionários':
            workers.workers_widget()

        case _:
            project = page

            tab = option_menu(None,
                              options=['Home', 'Cronograma', 'Equipa',
                                       'Sheet', 'Imputação', 'Custos'],
                              orientation="horizontal",
                              icons=['house', 'calendar2-week', 'person-vcard',
                                     'file-spreadsheet', 'hourglass', 'piggy-bank'],
                              styles={
                                  'container': {'max-width': '100%'}
                              },
                              key="project_page_selector",
                              )

            project = st.session_state.projects.query(
                'name == @project').iloc[0]

            match tab:

                case 'Home':

                    project_page.project_widget(project)

                case 'Cronograma':

                    timeline.timeline_widget(project)

                case 'Equipa':

                    team.team_widget(project)

                case 'Sheet':

                    sheet_page.sheet_widget(project)

                case 'Imputação':

                    time_allocation.time_allocation_widget(project)

                case 'Custos':

                    cost_allocation.cost_allocation_widget(project)

    add_keyboard_shortcuts({
        'Ctrl+Shift+S': '💾 Guardar',
        'Ctrl+Shift+s': '💾 Guardar',
        'Ctrl+z': '❌ Desfazer',
        'Ctrl+Z': '❌ Desfazer',
    })

    fade_notification()

    warning_before_leave()

    selected_operation()


if __name__ == "__main__":
    main()
