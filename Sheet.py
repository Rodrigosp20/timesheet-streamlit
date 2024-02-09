from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict
import pandas as pd
import numpy as np

@dataclass
class Sheet:
    salary: pd.DataFrame = field(default_factory= lambda: pd.DataFrame)
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

    def update_data_ranges(self, initial_date, end_date):
        #TODO: UPDATE SALARY
        months_range = pd.date_range(start=initial_date, end=end_date, freq='MS')
        date_range = [month.strftime('%b/%y') for month in months_range]

        df_work = pd.DataFrame(columns=date_range, index=['Jornada Diária', 'Dias Úteis', 'Faltas', 'Férias', 'Horas reais', 'Horas trabalhadas', 'FTE'])
        
        df_work.loc['Jornada Diária'] = 8
        df_work.loc['Dias Úteis'] = 20
        df_work.loc['Faltas'] = 0
        df_work.loc['Férias'] = 0
        df_work.loc['Horas reais'] = 0

        df_work = pd.merge(df_work, self.work)

        print(df_work)



    def update_wps(self, df, date_range):

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
    
    def update_computations(self):
        pass 
