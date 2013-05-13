# -*- coding:utf-8 -*-
'''
Created on 3 mai 2013

@author: Jérôme Santoul
'''

from src.lib.simulation import Simulation
from src.lib.cohorte import Cohorts
from pandas import DataFrame, read_csv, ExcelFile, HDFStore, read_table, concat
import matplotlib.pyplot as plt
import numpy as np
from numpy import hstack, array
import tables

"""
Attempting to recreate some graphs made by Carole BONNET in her paper : 
Carole Bonnet « Comptabilité générationnelle appliquée à la France : quelques facteurs d'instabilité des résultats », Economie & prévision 3/2002 (no 154), p. 59-78. 
URL : www.cairn.info/revue-economie-et-prevision-2002-3-page-59.htm. 
"""


population = read_csv('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\France\sources\data_fr\pop.csv', sep=',')
# print population.columns
population = population.set_index(['age', 'sex'])
population = population.stack()
population = population.reset_index()
population['level_2'] = population.level_2.convert_objects(convert_numeric=True)

population['year'] = population['level_2']
population['pop'] = population[0]
del population['level_2']
del population[0]
population = population.set_index(['age', 'sex', 'year'])

#Remove the years 2007 and beyond to ensure integrity when combined with INSEE data
year = list(range(1991, 2007, 1))
filter_year = array([x in year for x in population.index.get_level_values(2)])
population = population.iloc[filter_year, :]

#Loading insee data
projection = HDFStore('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\France\sources\data_fr\proj_pop_insee\proj_pop.h5', 'r')
projection_dataframe = projection['/projpop0760_FECbasESPbasMIGbas'] # <-Do not know the precise meaning of this. For testing only

#Combining
concatened = concat([population, projection_dataframe], verify_integrity = True)
concatened = concatened.reset_index()
concatened['year'] = concatened.year.convert_objects(convert_numeric=True)
concatened = concatened.set_index(['age', 'sex', 'year'])

#Saving as HDF5 file
export = HDFStore('neo_population.h5')
export.append('pop', concatened, data_columns = concatened.columns)
export.close()
export = HDFStore('neo_population.h5', 'r')
print export


#Creating the simulation object
net_payments = Simulation()
net_payments.set_population(population)
  
France = 'France'
net_payments.set_country(France)
r = 0.0
g = 0.01
net_payments.set_discount_rate(r)
net_payments.set_growth_rate(g)
# print net_payments
# print net_payments.growth_rate, net_payments.discount_rate, net_payments.country

net_payments.load_population("neo_population.h5", 'pop')
net_payments.load_profiles("C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\profiles.h5", "profiles.h5")
year_length = 100
net_payments.set_population_projection(year_length = year_length, method = "exp_growth", rate = 0.02)
net_payments.set_tax_projection(method = "per_capita", typ = None, rate = g, discount_rate = r)


net_payments.create_cohorts()

#Creating a column with total taxes paid.
for typ in net_payments._types:
    net_payments['total'] += hstack(net_payments[typ])
    
print net_payments['total']
