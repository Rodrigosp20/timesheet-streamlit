import streamlit as st
from utils import *
from itertools import product
from streamlit_tags import st_tags
import plotly.express as px

def update_timeline(project, data, executed, to_adjust):
    
    data['start_date'] = pd.to_datetime(data['start_date']).dt.date
    data['end_date'] = pd.to_datetime(data['end_date']).dt.date
    data['real_start_date'] = pd.to_datetime(data['real_start_date']).dt.date
    data['real_end_date'] = pd.to_datetime(data['real_end_date']).dt.date
    project['start_date'] = pd.to_datetime(project['start_date'])
    project['end_date'] = pd.to_datetime(project['end_date'])

    #Check ff dates are valid
    if ((data['start_date'] >= data['end_date']) | (data['real_start_date'] >= data['real_end_date'])).any():
        return set_notification("error", "Atividades com data inválidas!")
    
    #Check if there is any camp empty
    if data.isnull().values.any() or (data == '').values.any():
        return set_notification("error", "Campos em falta!")
    
    #Check if there are repeated activity names
    if data["activity"].nunique() != len(data["activity"]):
        return set_notification("error", "As Atividades tem de ter nomes únicos!")
    
    if executed and (executed < project['start_date'] or executed > project['end_date']):
        return set_notification("error", "Data de execução inválida!")
    
    st.session_state.projects.loc[st.session_state.projects["name"] == project["name"], 'executed'] = executed.date() if executed else None
    
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
                    filter = (df['person'] == contract.person) & (df['date'] > pd.to_datetime(executed)) & (df['activity'] == act)
                
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

    st.session_state.planned_work = st.session_state.planned_work.query('~ (project == @project["name"] and activity not in @data["activity"].unique())')
    st.session_state.activities = st.session_state.activities.query('project != @project["name"]')
    st.session_state.activities = pd.concat([st.session_state.activities, data])
    set_notification("success", "Cronograma atualizado com sucesso!", force_reset=True)

@st.cache_data
def get_gantt(project, timeline):
    result = timeline.groupby('wp').agg({'start_date': 'min', 'end_date': 'max', 'real_start_date': 'min', 'real_end_date': 'max'})

    gantt_data = []
    last_wp = None
    for act in timeline.itertuples():
        if last_wp != act.wp:
            wp = result.loc[act.wp]
            gantt_data.append({
                'Task': act.wp,
                'Start': wp['start_date'],
                'Finish': wp['end_date'],
                'Color': "Planeado"
            })
    
            if project['executed'] and project['executed'] > wp['real_start_date']:
                gantt_data.append({
                    'Task': act.wp,
                    'Start': wp['real_start_date'],
                    'Finish': project['executed'],
                    'Color': "Executado"
                })

            if wp['start_date'] != wp['real_start_date'] or wp['end_date'] != wp['real_end_date']:
                gantt_data.append({
                    'Task': act.wp,
                    'Start': wp['real_start_date'],
                    'Finish': wp['real_end_date'],
                    'Color': "Real"
                })
            
            last_wp = act.wp

        gantt_data.append({
            'Task': act.activity,
            'Start': act.start_date,
            'Finish': act.end_date,
            'Color': "Planeado"
        })

        if project['executed'] and project['executed'] > act.real_start_date:
            gantt_data.append({
                'Task': act.activity,
                'Start': act.real_start_date,
                'Finish': project['executed'],
                'Color': "Executado"
            })

        if act.start_date != act.real_start_date or act.end_date != act.real_end_date:   
            gantt_data.append({
                'Task': act.activity,
                'Start': act.real_start_date,
                'Finish': act.real_end_date,
                'Color': f"Real"
            })

    return gantt_data

def timeline_widget(project):
    timeline = st.session_state.activities.query("project == @project['name']")
    timeline = timeline.sort_values(by=['wp', 'activity', "start_date"])

    #SAFE DATES
    timeline['start_date'] = pd.to_datetime(timeline['start_date']).dt.date
    timeline['end_date'] = pd.to_datetime(timeline['end_date']).dt.date
    timeline['real_start_date'] = pd.to_datetime(timeline['real_start_date']).dt.date
    timeline['real_end_date'] = pd.to_datetime(timeline['real_end_date']).dt.date
    
    gantt_data = get_gantt(project, timeline)

    project['start_date'] = pd.to_datetime(project['start_date'])
    project['end_date'] = pd.to_datetime(project['end_date'])


    save, undo = get_topbar(project['name'])

    st.subheader("Cronograma")
    if len(gantt_data) > 0:
        gantt_df = pd.DataFrame(gantt_data)

        fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="Color", color_discrete_map={'Planeado':"#0AA3EB", "Real":"#DAF1FC", "Executado":"#878787"}, category_orders={'Color': ["Planeado","Real","Executado"]})
        fig.update_yaxes(autorange="reversed")
        for i in range(1,len(fig.data)):
            fig.data[i].width = 0.5 
        
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write('<p style="text-align: center;">Sem Dados Disponíveis</p>', unsafe_allow_html=True)

    
    executed_date = pd.to_datetime(st.date_input("Data de execução do projeto [bloqueada]", value=project['executed'], min_value=project['start_date'], max_value=project['end_date'], format="DD/MM/YYYY"))
    
    st.subheader("WPs do Projeto")
    wps = list(timeline['wp'].unique())
    wps = st.data_editor(
        wps if wps else [''],
        column_config={
            "value":st.column_config.TextColumn("Workpackage", required=True)
        },
        num_rows="dynamic",
        hide_index=True,
        key=f"wps_list_{st.session_state.key}"
    )

    activities = timeline.query('wp in @wps')
    activities = activities.set_index('activity')
    
    to_update = pd.DataFrame(columns=activities.columns)

    col1 , col2 = st.columns([0.35,0.65])

    if '' in wps:
        wps.remove('')
    
    to_adjust = False
    
    
    if not wps:
        st.write('<p style="text-align: center;">Nenhum WP Encontrado</p>', unsafe_allow_html=True)
    
    else:
        col1.subheader("Atividades do Projeto")    
        to_adjust  = col2.toggle("Ajuste Automático das Horas Planeadas")


        for wp in wps:

            with st.expander(wp, expanded=True):                    
                wp_df = activities.query('wp == @wp')

                wp_acts = st.data_editor(
                    wp_df,
                    key=f"{wp}_data_{st.session_state.key}",
                    column_order=["activity", "trl", "start_date", "end_date", "real_start_date", "real_end_date"],
                    column_config={
                        "activity": st.column_config.TextColumn(
                            "Atividade",
                            required=True,
                            default="A",
                            width="medium",
                        ),
                        "trl": st.column_config.SelectboxColumn(
                            "TRL",
                            options=['TRL 3-4', 'TRL 5-9'],
                            required=True
                        ),
                        "start_date": st.column_config.DateColumn(
                            "Data de Inicio [Planeada]",
                            min_value=project["start_date"],
                            default=project["start_date"],
                            format="DD/MM/YYYY",
                            required=True
                        ),
                        "end_date": st.column_config.DateColumn(
                            "Data de Conclusão [Planeada]",
                            max_value=project["end_date"],
                            default=project["end_date"],
                            format="DD/MM/YYYY",
                            required=True
                        ),
                        "real_start_date": st.column_config.DateColumn(
                            "Data de Inicio [Real]",
                            min_value=project["start_date"] if not project['executed'] else project['executed'],
                            max_value=project["end_date"],
                            default=project["start_date"],
                            format="DD/MM/YYYY",
                            required=True
                        ),
                        "real_end_date": st.column_config.DateColumn(
                            "Data de Conclusão [Real]",
                            min_value=project["start_date"] if not project['executed'] else project['executed'],
                            max_value=project["end_date"],
                            default=project["end_date"],
                            format="DD/MM/YYYY",
                            required=True
                        )
                    },
                    use_container_width=True,
                    num_rows='dynamic'
                )

                wp_acts[['wp', 'project']] = [wp, project['name']]
                to_update = pd.concat([to_update, wp_acts])

  

    if save:        
        # NONE EMPTY CELLS; Nomes unicos de tarefas         
        update_timeline(project, to_update.reset_index(names="activity"), executed_date, to_adjust)
    
    if undo:
        reset_key()
