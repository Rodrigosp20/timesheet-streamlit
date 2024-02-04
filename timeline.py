import streamlit as st
import plotly.figure_factory as ff
import pandas as pd
import datetime

def timeline_tab():
    st.title("Cronograma")
    
    # Sidebar for adding new entries
    st.sidebar.header("Add New Entry")

    selected_item_type = st.sidebar.radio("Select Item Type", ['Work Package', 'Activity', 'Task'])

    if selected_item_type == 'Work Package':

        new_work_package_name = st.sidebar.text_input("New Work Package Name", key='new_work_package_name')

        if st.sidebar.button("Add Work Package"):
            if new_work_package_name not in st.session_state.data:
                st.session_state.data[new_work_package_name] = {}
                st.sidebar.success("Work Package added successfully!")

    elif selected_item_type == 'Activity':
        selected_work_package = st.sidebar.selectbox("Select Work Package", list(st.session_state.data.keys()), key='selected_work_package_activity')
        if selected_work_package:
            new_activity_name = st.sidebar.text_input("New Activity Name", key='new_activity_name')

            trl = st.sidebar.selectbox("TRL", options=['TRL 3-4', 'TRL 5-9'])

            if st.sidebar.button("Add Activity"):
                if new_activity_name not in st.session_state.data[selected_work_package]:
                    st.session_state.data[selected_work_package][new_activity_name] = {'trl':trl, "tasks":{}}
                    st.sidebar.success("Activity added successfully!")

    elif selected_item_type == 'Task':
        selected_work_package_task = st.sidebar.selectbox("Select Work Package", list(st.session_state.data.keys()), key='selected_work_package_task')
        
        if selected_work_package_task:
            
            selected_activity_task = st.sidebar.selectbox("Select Activity", list(st.session_state.data[selected_work_package_task].keys()), key='selected_activity_task')
            if selected_activity_task:
                
                new_task_name = st.sidebar.text_input("New Task Name", key='new_task_name')
                
                start_date = st.sidebar.date_input("Select Start Date", key='start_date', format="DD/MM/YYYY", value=None)
                min_end_date = (start_date + datetime.timedelta(days=1)) if start_date else None
                end_date = st.sidebar.date_input("Select End Date", min_value=min_end_date, key='end_date', format="DD/MM/YYYY", value=None)

                if st.sidebar.button("Add Task", disabled = not new_task_name or not start_date or not end_date):
                    new_task = {
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                    st.session_state.data[selected_work_package_task][selected_activity_task][new_task_name] = new_task
                    st.sidebar.success("Task added successfully!")

    
    gantt_data = []
    for work_package, activities in st.session_state.data.items():
        for activity, activity_content in activities.items():
            for task, content in activity_content['tasks'].items():
                gantt_data.append({
                    'Task': f'{work_package} - {activity} - {task}',
                    'Start': content['start_date'],
                    'Finish': content['end_date'],
                    'Resource': work_package
                })

    if len(gantt_data) > 0:
        gantt_df = pd.DataFrame(gantt_data)

        colors = {'a': 'rgb(220, 0, 0)'}

        # Gantt chart using Plotly
        fig = ff.create_gantt(gantt_df, colors="Viridis",  index_col='Resource', show_colorbar=True, group_tasks=True)
        
        # Display Gantt chart using HTML
        st.plotly_chart(fig)