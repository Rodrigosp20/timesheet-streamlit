from dataclasses import dataclass, field
from datetime import date
from Sheet import Sheet
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

    def change_date(self, initial_date, end_date):
        initial_date = initial_date.date()
        end_date = end_date.date()
        
        for act in self.activities.itertuples():
            if act[4] < initial_date:
                self.activities.at[act.Index, 'Data Inicio'] = initial_date
            
            if act[5] > end_date:
                self.activities.at[act.Index, 'Data Fim'] = end_date
        
        for member in self.team.itertuples():
            if member[4] < initial_date:
                self.team.at[member.Index, 'Data Inicio'] = initial_date

            if member[5] > end_date:
                self.team.at[member.Index, 'Data Fim'] = end_date

        for sheet in self.sheets.values():
            sheet.update_data_ranges(initial_date, end_date)
                

    
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
        
        # Reflect changes to all sheets
        for member in new_team.itertuples(index=False):
            
            if member.Nome in self.sheets.keys():
                #TODO: UPDATE SALARY SHEET IF APPLICABLE
                continue
            
            self.sheets[member.Nome] = Sheet.custom_constructor(self.activities, self.get_date_column())
            #self.sheets[member.Nome].update_computations()
        
    def get_member_salary(member):
        pass
        