import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import datetime
from team import team_tab
from timeline import timeline_tab
from classes import *


def recalculate_horas_trabalhadas(df):
    df_calcs = pd.DataFrame(columns=df.columns, index=['Horas trabalhadas', 'FTE'])

    df_calcs.loc['Horas trabalhadas'] = df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Faltas'] - df.loc['Férias']
    df_calcs.loc['FTE'] = df.loc['Horas reais'] / (df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Férias'])

    return df_calcs

def update_sheets():
    for person in st.session_state.project['persons'].itertuples(index=False):

        if person.Nome not in st.session_state.project['sheets'].values():

            person_sheets = {}
            
            start_date = st.session_state.project['start_date']
            end_date = st.session_state.project['end_date']

            months_range = pd.date_range(start=start_date, end=end_date, freq='MS')
            formatted_columns = [month.strftime('%b/%y') for month in months_range]

            df = pd.DataFrame(columns=formatted_columns, index=['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas reais', 'Horas trabalhadas', 'FTE'])
            
            df.loc['Jornada Diária'] = 8
            df.loc['Dias Úteis'] = 20
            df.loc['Faltas'] = 0
            df.loc['Férias'] = 0
            df.loc['Horas reais'] = 0
            
            df.loc['Horas trabalhadas'] = df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Faltas'] - df.loc['Férias']
            df.loc['FTE'] = df.loc['Horas reais'] / (df.loc['Jornada Diária'] * df.loc['Dias Úteis'] - df.loc['Férias'])

            person_sheets['sheet'] = df

            for wp, activites in st.session_state.project['timeline'].items():

                df = pd.DataFrame(columns=['TRL']+formatted_columns, index=activites.keys())
                for act in activites.keys():
                    df.loc[act,'TRL'] = st.session_state.project['timeline'][wp][act]['trl']

                df.loc[:, df.columns != 'TRL'] = 0

                person_sheets[wp] = df
        
        else:
            pass
            #TODO: Modify Dataframe

        st.session_state.project['sheets'][person.Nome] = person_sheets

def validate_activities_form(acts, wps):

    for wp in wps:
        if acts[acts['WP'] == wp].empty:
            return f"{wp} não tem nenhuma atividade associada"
    
    return None

def main():

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Projeto", "Cronograma", "Equipa", "Pessoal", "Imputação"])

    # Initialize data structure      
    if 'projects' not in st.session_state:
        st.session_state.projects = {
            "BLM" : Project(start_date=datetime.date(year=2024, month=1, day=1), end_date=datetime.date(year=2026, month=12, day=31))
        }
    
    if 'project' not in st.session_state:
        st.session_state.project = None
        st.session_state.project_name = ""

    if 'key' not in st.session_state:
        st.session_state.key = 0 

    with tab1:

        if not st.session_state.project:
            st.session_state.project_name = st.selectbox('Select a Project', [""] + list(st.session_state.projects.keys()))
            st.session_state.project = st.session_state.projects.get(st.session_state.project_name)
            
            if st.session_state.project:
                st.rerun()
        
        if st.session_state.project:
            st.title(f"{st.session_state.project_name}")

            project = st.session_state.project

            start_date = st.date_input("Data Inicio", value=project.start_date, format="DD/MM/YYYY")
            end_date = st.date_input("Data Fim", value=project.end_date, format="DD/MM/YYYY")

            if st.button("Save changes"):
                #APPLY CHANGES TO ALL PROJECT DATAFRAMES IF THEY EXIST
                project['start_date'] = start_date
                project['end_date'] = end_date

                st.experimental_rerun()
                
    with tab2:
        
        if project := st.session_state.project:
            
            st.title("Gantt")
            gant = st.session_state.project.get_gant()

            if len(gant) > 0:
                gantt_df = pd.DataFrame(gant)
                fig = ff.create_gantt(gantt_df, colors="Viridis",  index_col='Resource', show_colorbar=True, group_tasks=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Não foram adicionadas atividades ao projeto")
            
            tab_wp, tab_act = st.tabs(["Workpackage","Activty"])

            with tab_wp:
                project = st.session_state.project

                st.title('WP')
                wp_list = st.data_editor(
                    np.array(project.wps),
                    hide_index=True,
                    key=f"wp_{st.session_state.key}",
                    column_config={
                        "value": st.column_config.TextColumn(
                            "Nome",
                            required=True,
                            width="large",

                        )
                    },
                    num_rows='dynamic'
                )
            
                st.title('Atividades')
                act_list = st.data_editor(
                    project.activities,
                    key=f"act_{st.session_state.key}",
                    column_config={
                        "WP": st.column_config.SelectboxColumn(
                            "WP",
                            options=wp_list,
                            required=True
                        ),
                        "TRL": st.column_config.SelectboxColumn(
                            "TRL",
                            options=['TRL 3-4', 'TRL 5-9'],
                            required=True
                        ),
                        "Data Inicio": st.column_config.DateColumn(
                            "Data Inicio",
                            min_value=project.start_date,
                            default=project.start_date,
                            format="DD/MM/YYYY",
                            required=True
                        ),
                        "Data Fim": st.column_config.DateColumn(
                            "Data Fim",
                            min_value=project.end_date,
                            default=project.end_date,
                            format="DD/MM/YYYY",
                            required=True
                        )
                    },
                    hide_index=True,
                    num_rows="dynamic",
                    use_container_width=True
                )

                if st.button("Save Changes", key="wp"):
                    act_list = act_list[act_list['WP'].isin(wp_list)]
                    
                    if not (error := validate_activities_form(act_list, wp_list)):
                        project.update_activities(act_list, wp_list)
                        st.rerun()
                    else:
                        st.write(error)
                        
           
                if st.button("Discard Changes"):
                    st.session_state.key = (st.session_state.key + 1) % 2
                    st.rerun()

                


            with tab_act:
                pass
        
        #timeline_tab()

    with tab3:
        
        st.title(f"Perfis do {st.session_state.project_name}")
        
        if project := st.session_state.project:

            new_team = st.data_editor(
                project.team, 
                num_rows="dynamic",
                column_config = {
                    "Perfil": st.column_config.TextColumn(
                        "Perfil",
                        width = "medium",
                        required = True,
                    ),
                    "Nome": st.column_config.TextColumn(
                        "Nome",
                        width = "medium",
                        required = True,
                    ),
                    "Genero": st.column_config.SelectboxColumn(
                        "Genero",
                        options = ["M", "F"],
                        width="small",
                        required = True,
                    ),
                    "Data Inicio": st.column_config.DateColumn(
                        "Data Inicio",
                        format="DD/MM/YYYY",
                        default=project.start_date,
                        step=1,
                    ),
                    "Data Fim": st.column_config.DateColumn(
                        "Data Fim",
                        format="DD/MM/YYYY",
                        default=project.end_date,
                        step=1,
                    ),
                },
                use_container_width = True,
                hide_index=True
            )

            if st.button("Save Changes", key="save_profiles"):
                project.update_team(new_team)
                #update_sheets()
                #CREATE OR MODIFY SHEETS FOR EACH PERSON
                st.rerun()
            
    
    with tab4:
        project = st.session_state.project

        if member := st.selectbox("Person", options= st.session_state.project.team['Nome'].to_list()):

            sheet = project.sheets[member]

            modifications = st.data_editor(
                sheet.work.iloc[0:5],
                key = f"{member}_sheet",
                use_container_width=True
            )

            result = recalculate_horas_trabalhadas(modifications)

            if saved_clicked := st.button("Save Changes"):
                project.sheets[member].work.iloc[0:5] = modifications.copy()
                project.sheets[member].work.iloc[5:] = result.copy()

            st.dataframe(result)

            all_wps = pd.DataFrame(columns= ['WP', 'TRL'].append(modifications.columns))
            for wp, df in sheet.wps.items():
                    
                st.title(wp)
                
                wp_modifications = st.data_editor(
                    df,
                    key = f"{member}_{wp}",
                    disabled=["TRL"],
                    use_container_width=True
                )

                if saved_clicked:
                    project.sheets[member].wps[wp] = wp_modifications

                to_wp = wp_modifications.copy()
                to_wp.insert(0, 'WP', wp)
                all_wps = pd.concat([all_wps, to_wp])
            
            if not all_wps.empty:
                wp_sum = all_wps.drop('TRL', axis=1).groupby(['WP']).sum().reset_index()
                st.dataframe(wp_sum.set_index('WP'))

                total_wp_sum = all_wps.iloc[:, 2:].sum(axis=0)
                total_wp_sum[total_wp_sum == 0] = np.nan

                horas_reais = modifications.loc['Horas reais']
                jornada_diaria = modifications.loc['Jornada Diária']
                dias_uteis = modifications.loc['Dias Úteis']

                all_wps.iloc[:,2:] = (
                    all_wps.iloc[:, 2:].div(total_wp_sum, axis=1)
                    .mul(horas_reais)
                    .div(jornada_diaria.mul(dias_uteis))
                )

                # Replace inf and nan with 0
                all_wps.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

                if saved_clicked:
                    project.sheets[member].computations = all_wps
                    st.rerun()
                    
                st.title("Afetação Atividade")
                st.dataframe(all_wps.iloc[:,2:])
                
                group_wp = all_wps.groupby(['WP','TRL']).sum().reset_index()

                st.title("Afetação WP/TRL")
                st.dataframe(group_wp.set_index(['WP', 'TRL']))

            
    with tab5:

        project = st.session_state.project

        fte = pd.DataFrame(0.0, columns=project.get_date_column(), index=["FTE's Globais", "FTE's Femininos", "FTE's Masculinos"])
        
        project = st.session_state.project
        for person in project.team.loc[:, ['Nome', 'Genero']].itertuples(index=False):
            
            person_sheet = project.sheets[person.Nome]
            gender_index = 1 if person.Genero == 'F' else 2

            fte.iloc[0] = fte.iloc[0] +  person_sheet.work.loc['FTE']
            fte.iloc[gender_index] = fte.iloc[gender_index] +  person_sheet.work.loc['FTE']

        st.dataframe(fte)
        
        person_total_hours = pd.DataFrame(columns=["Person","WP"]+project.get_date_column())
        person_wp_trl_hours = pd.DataFrame(columns=["Person","WP","TRL"]+project.get_date_column())
        for person in project.team.itertuples(index=False):

            person_sheet = project.sheets[person.Nome]

            if not (person_afetacao := person_sheet.computations).empty :
                
                #person_total_hours.loc[len(person_total_hours)] =  
                by_wp = person_afetacao.drop('TRL', axis=1).groupby('WP').sum().reset_index()
                by_wp.iloc[:,1:] = by_wp.iloc[:,1:] * pd.to_numeric(person_sheet.work.loc['Horas reais'])
                by_wp.insert(0,'Person',person.Nome)

                by_wp_trl = person_afetacao.groupby(['WP', 'TRL']).sum().reset_index()
                
                by_wp_trl.iloc[:,2:] = by_wp_trl.iloc[:,2:] * pd.to_numeric(person_sheet.work.loc['Horas reais'])
                by_wp_trl.insert(0,'Person',person.Nome)
                
                
                person_total_hours = pd.concat([person_total_hours, by_wp])
                person_wp_trl_hours = pd.concat([person_wp_trl_hours, by_wp_trl])
        
        st.dataframe(person_total_hours.drop('Person', axis=1).groupby('WP').sum().reset_index())


        
        st.dataframe(person_total_hours, hide_index=True)
        st.dataframe(person_wp_trl_hours)
                


                
                
            




        
        
    
if __name__ == "__main__":
    main()
