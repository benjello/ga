# -*- coding:utf-8 -*-
# Created on 6 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from __future__ import division
import os
from src.lib.simulation import Simulation
from src.lib.cohorte import Cohorts
from pandas import read_csv, HDFStore, concat, ExcelFile, Series
from numpy import array, hstack
import matplotlib.pyplot as plt
from src import SRC_PATH




def test():
    
#     Previous attempt to fuse INSEE and the pop data of C Bonnet

#     population = read_csv('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\France\sources\data_fr\pop.csv', sep=',')
#     # print population.columns
#     population = population.set_index(['age', 'sex'])
#     population = population.stack()
#     population = population.reset_index()
#     population['level_2'] = population.level_2.convert_objects(convert_numeric=True)
# 
#     population['year'] = population['level_2']
#     population['pop'] = population[0]
#     del population['level_2']
#     del population[0]
#     population = population.set_index(['age', 'sex', 'year'])
#     #Remove the years 2007 and beyond to ensure integrity when combined with INSEE data
#     year = list(range(1991, 2007, 1))
#     filter_year = array([x in year for x in population.index.get_level_values(2)])
#     population = population.loc[filter_year, :]
    
    
#     population.append_to_multiple(population_filename, "table", append = True)
#     #Loading insee data
#     projection = HDFStore('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\France\sources\data_fr\proj_pop_insee\proj_pop.h5', 'r')
#     projection_dataframe = projection['/projpop0760_FECbasESPbasMIGbas']
#  
#     #Combining
#     concatened = concat([population, projection_dataframe], verify_integrity = True)
#     concatened = concatened.reset_index()
#     concatened['year'] = concatened.year.convert_objects(convert_numeric=True)
#     concatened = concatened.set_index(['age', 'sex', 'year'])
#  
#     #Saving as HDF5 file
#     export = HDFStore('neo_population.h5')
#     export.append('pop', concatened, data_columns = concatened.columns)
#     export.close()
#     export = HDFStore('neo_population.h5', 'r')

    country = "france"    
    population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
    profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','profiles.h5')

    CBonnet_results = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'theoretical_results.xls')

    simulation = Simulation()
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
        
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    xls = ExcelFile(CBonnet_results)
    """
    Hypothesis set #1 : 
    actualization rate r = 3%
    growth rate g = 1%
    """
    r = 0.03

    g = 0.01
    simulation.set_discount_rate(r)
    simulation.set_growth_rate(g)
    
    #Setting parameters
    year_length = 100

    simulation.set_population_projection(year_length=year_length, method="exp_growth")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()

#     print simulation.cohorts.head()
    print simulation.cohorts._types

    #Calculating net transfers
    #Net_transfers = money recieved from the state minus tax paid (state point of view)
    
    simulation.cohorts['total_taxes'] = 0
    simulation.cohorts['total_payments'] = 0
    
    set_taxes = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    set_payments = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    for typ in set_taxes:
        simulation.cohorts['total_taxes'] += hstack(simulation.cohorts[typ])
    for typ in set_payments:
        simulation.cohorts['total_payments'] += hstack(simulation.cohorts[typ])
    
    simulation.cohorts['net_transfers'] = simulation.cohorts['total_taxes'] - simulation.cohorts['total_payments']
    simulation.cohorts._types = ([u'tva', u'tipp', u'cot', u'irpp', u'impot',
                                   u'property', u'chomage', u'retraite', 
                                   u'revsoc', u'maladie', u'educ', u'net_transfers'])
    
    
    """
    Reproducing the table 2 : Comptes générationnels par âge et sexe (Compte central)
    """
    #Generating generationnal accounts
    per_capita_present_value = Cohorts(simulation.cohorts.per_capita_generation_present_value(typ = 'net_transfers', discount_rate = simulation.discount_rate))
    print "PER CAPITA PV"
    print per_capita_present_value.xs(0, level = 'age').head()
    print per_capita_present_value.xs((0, 2007), level = ['sex', 'year']).head()


    # Calculating the Intertemporal Public Liability
    aggregated_present_value = Cohorts(simulation.cohorts.aggregate_generation_present_value(typ = 'net_transfers', discount_rate = simulation.discount_rate))
    ipl = aggregated_present_value.compute_ipl(typ = 'net_transfers')
    print "----------------------------------"
    print "ipl =", ipl
    print "----------------------------------"


    #Creating age classes
    cohorts_age_class = Cohorts(per_capita_present_value.create_age_class(step = 5))
    cohorts_age_class._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe = cohorts_age_class.xs((1, 2007), level = ['sex', 'year'])
    age_class_pv_ma = cohorts_age_class.xs((0, 2007), level = ['sex', 'year'])
    print "AGE CLASS PV"
    print age_class_pv_fe
    print age_class_pv_ma
    
    """
    TODO: there is a problem with the last age class : in the paper it includes people from 95 to 100 years old. 
    However the program seperates the 100 years old and more from the others
    """
    
    #Plotting
    age_class_pv = cohorts_age_class.xs(2007, level = "year").unstack(level="sex")
    age_class_pv = age_class_pv['net_transfers']
    age_class_pv.columns = ['men' , 'women']
#     age_class_pv['total'] = age_class_pv_ma['net_transfers'] + age_class_pv_fe['net_transfers']
#     age_class_pv['total'] *= 1.0/2.0
    age_class_theory = xls.parse('Feuil1', index_col = 0)
     
    age_class_pv['men_CBonnet'] = age_class_theory['men_Cbonnet']
    age_class_pv['women_CBonnet'] = age_class_theory['women_Cbonnet']
    age_class_pv.plot(style = '--') ; plt.legend()
    plt.axhline(linewidth=2, color='black')
    plt.show()
     
if __name__ == '__main__':
    test()

