from dataclasses import dataclass, field
import pickle
from datetime import date
from typing import List, Dict
import pandas as pd
import numpy as np


empty_person = {
    'Perfil': str,
    'Nome': str,
    'Genero': str,
    'Data Inicio': 'datetime64[ns]',
    'Data Fim': 'datetime64[ns]'
}

empty_activities = {
    'WP': str,
    'Atividade': str,
    'TRL': str,
    'Data Inicio': 'datetime64[ns]',
    'Data Fim': 'datetime64[ns]'
}

def create_empty_df(columns_type):
    df = pd.DataFrame(columns= columns_type.keys())
    df = df.astype(columns_type)
    return df


@dataclass
class Sheet:
    salary: List[tuple] = None
    work: pd.DataFrame = field(default_factory= lambda: pd.DataFrame)
    wps: dict[str, pd.DataFrame] = None
    computations: pd.DataFrame = field(default_factory= lambda: pd.DataFrame)

    @classmethod
    def custom_constructor(cls, activites, date_range):

        df_work = pd.DataFrame(columns=date_range, index=['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas reais', 'Horas trabalhadas', 'FTE'])
        
        df_work.loc['Jornada Diária'] = 8
        df_work.loc['Dias Úteis'] = 20
        df_work.loc['Faltas'] = 0
        df_work.loc['Férias'] = 0
        df_work.loc['Horas reais'] = 0
        
        df_work.loc['Horas trabalhadas'] = df_work.loc['Jornada Diária'] * df_work.loc['Dias Úteis'] - df_work.loc['Faltas'] - df_work.loc['Férias']
        df_work.loc['FTE'] = df_work.loc['Horas reais'] / (df_work.loc['Jornada Diária'] * df_work.loc['Dias Úteis'] - df_work.loc['Férias'])

        wps = {}
        for wp in activites['WP'].unique():
            activities_list= activites[activites['WP'] == wp]['Atividade'].tolist()

            df = pd.DataFrame(columns=['TRL']+date_range, index=activities_list)
            for act in activities_list:
                df.loc[act,'TRL'] = activites[activites['Atividade'] == act].iloc[0,2]

            df.loc[:, df.columns != 'TRL'] = 0

            wps[wp] = df

        return cls(work=df_work, wps=wps)


    def update_team_wps(self, df, date_range):

        df = df.iloc[:,0:2].groupby(['WP']).agg(list).reset_index()
        print(df)
        return
        for wp, df_wp in self.wps: 
            #Remove wp if dont exist anymore
            if wp not in df['WP']:
                del self.wps[wp]
                continue

            activity_list = df[df['WP'] == wp].loc['activities']

            #Remove non existing activites from the wp
            df_wp = df_wp[df_wp.index.isin(activity_list)]

            #Add non existing activities to the wp
            for index in activity_list:
                if index not in df_wp.index:
                    df_wp = df_wp.append(pd.DataFrame(0, columns=df_wp.columns, index=[index]))

            df = df[df['WP'] != wp]
            df_wp = df_wp.sort_index()

        #Create new wps if dont exist
        for line in df.itertuples(index=False):

            df_wp = pd.DataFrame(columns=['TRL']+date_range, index=line.activities)
            for act in line.activities:
                df_wp.loc[act,'TRL'] = line.TRL

            df_wp.loc[:, df_wp.columns != 'TRL'] = 0

            self.wps[line.WP] = df_wp
        
        #RECALCULATE COMPUTATIONS DATAFRAMES
            
@dataclass
class Project:
    start_date: date
    end_date: date
    wps: List[str] = field(default_factory=lambda: [""])
    activities: pd.DataFrame = field(default_factory= lambda: create_empty_df(empty_activities))
    modifications_activities: Dict[str, List] = None
    team: pd.DataFrame = field(default_factory= lambda: create_empty_df(empty_person))
    sheets: Dict[str, Sheet] = field(default_factory=dict)
    
    def get_gant(self):
        gant = []

        for act in self.activities.itertuples(index=False):
            gant.append({
                'Task': act.Atividade,
                'Start': act[3],
                'Finish': act[4],
                'Resource': act.WP
            })

        return gant

    def get_date_column(self):
        months_range = pd.date_range(start=self.start_date, end=self.end_date, freq='MS')
        return [month.strftime('%b/%y') for month in months_range]

    def change_date():
        pass
    
    def update_activities(self, df: pd.DataFrame, wps: np.array):

        if len(wps) == 0:
            self.wps = create_empty_df(empty_activities)
            self.activities = create_empty_df(empty_person)
        else:
            self.wps = np.copy(wps)
            self.activities = df.copy()

        for sheet in self.sheets.values():
            sheet.update_team_wps(df, self.get_date_column())


    def update_team(self, new_team: pd.DataFrame):
        self.team = new_team.copy()

        #Delete all non existing members in sheets
        self.sheets = {person: value for person, value in self.sheets.items() if person in new_team['Nome']}
        
        #Create the default sheets for new members
        for member in new_team.itertuples(index=False):
            
            if member.Nome in self.sheets.keys():
                continue
            
            self.sheets[member.Nome] = Sheet.custom_constructor(self.activities, self.get_date_column())
        

    def get_member_salary(member):
        pass


@dataclass
class Activity:
    trl: str
    start_date: date
    end_date: date
    modifications: List[tuple]

    def define_initial_date(self, start_date :date, end_date:date) -> None:
        self.start_dates.insert(0, start_date)
        self.end_dates.insert(0, end_date)



            



"""project = Project(start_date=date(year=2024, month=1, day=1), end_date=date(year=2027, month=12, day=31))

act = Activity(name="Atividade 1- inicio")
act.define_initial_date(start_date=date(year=2024, month=1, day=1), end_date=date(year=2024, month=12, day=31))

project.timeline['Atividade 1'] = act

with open('my_data_instance.pkl', 'wb') as file:
    pickle.dump(project, file)

# Load the dataclass instance from the file
with open('my_data_instance.pkl', 'rb') as file:
    project2 = pickle.load(file)

print(project2)"""
