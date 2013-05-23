# -*- coding:utf-8 -*-
'''
Created on 26 avr. 2013

@author: Mahdi Ben Jelloul, Jérôme Santoul
'''

from pandas import DataFrame, merge
from numpy import arange
from src.lib.cohorte import Cohorts
from src.lib.DataCohorts import DataCohorts

#===============================================================================
# Some function to generate fake data for testing
#===============================================================================

def create_empty_population_dataframe(year_start, year_end, population = None):
    # Building population and profiles dataframes 
    # with ones everywhere
    # the length of the dataframe can be adjusted
    if population is None:
        population = 1 
    df_age = DataFrame({ 'age': range(0,101)})
    df_sex = DataFrame({ 'sex': [0,1],})
    df_year = DataFrame({ 'year': range(year_start,year_end)})
    df_age['key'] = 1
    df_sex['key'] = 1    
    df_year['key'] = 1 
    df = merge(df_age, df_sex,on='key')[['age', 'sex']]
                      
    df['key'] = 1
    df2 = merge(df, df_year,on='key')[['age', 'sex','year']]
    population_dataframe = df2.set_index(['age', 'sex','year'])
    population_dataframe['pop'] = population
    return population_dataframe


def create_testing_population_dataframe(year_start = None, year_end = None, rate = None, population = None):
    """
    """
    if year_start is None or year_end is None:
        year_start = 2001
        year_end = 2003
    if population is None:
        population = 1 
    if rate is None:       
        population_dataframe = create_empty_population_dataframe(year_start, year_end, population)
    else:
        population_dataframe = create_empty_population_dataframe(year_start, year_end, population)
#         created classic dataframe with constant population, now updating with growth 
      
        population_dataframe['grth'] = 1
        grouped = population_dataframe.groupby(level = ['sex', 'age'])['grth']
        nb_years = year_end-year_start
        population_dataframe['grth'] = grouped.transform(lambda x: (1+rate)**(arange(nb_years)))
        population_dataframe['pop'] = population_dataframe['pop']*population_dataframe['grth']
        del population_dataframe['grth']

    return population_dataframe

def create_constant_profiles_dataframe(population_dataframe, **kwargs):
    """
    Function which creates a profile dataframe with a single year index
    """
    temp = zip(*population_dataframe.index)
    year_min = min(temp[2])
    population_dataframe.reset_index(inplace=True)
    profiles_dataframe = population_dataframe[population_dataframe.year==year_min]
    population_dataframe.set_index(["age","sex","year"],inplace=True)   
    for key, value in kwargs.iteritems():
        profiles_dataframe[key] = value
    del profiles_dataframe["pop"]
    profiles_dataframe.set_index(["age","sex","year"],inplace=True)
    return profiles_dataframe


def create_neutral_profiles_cohort(population):
    """
    Utility function which generates a DataCohort with population and transfers.
    No projection is needed, the dataframe is delivered without "hole"
    
    Parameters
    ----------
    population : Int
                 The value of the constant population at each period and for each age
    
    Returns
    -------
    cohort : a cohort dataframe such that :
            Anybody below 50 years old (excluded) pays -1
            Anybody between 50 and 99 years old (included) recieve 1
            Anybody over 100 years old (included) pays 0
            As such, the total net transfer is zero for newborns
    """
    n = 0
    population_dataframe = create_testing_population_dataframe(year_start=2001, year_end=2201, rate=n, population=population)
#     print population.get_value((0,0,2011), 'pop')
    profile = create_constant_profiles_dataframe(population_dataframe, tax=-1)
    g = 0.0
    r = 0.0 
    cohort = DataCohorts(population_dataframe)
    cohort.fill(profile)
    cohort.loc[cohort.index.get_level_values(0) >= 0,'tax'] = -1
    cohort.loc[cohort.index.get_level_values(0) >= 50,'tax'] = 1
    cohort.loc[cohort.index.get_level_values(0) == 100,'tax'] = 0
    typ = 'tax'
    cohort.proj_tax(g, r, typ,  method = 'per_capita')

    return cohort


if __name__ == '__main__':
    pass