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
from src.lib.AccountingCohorts import AccountingCohorts
from pandas import read_csv, HDFStore, concat, ExcelFile, Series
from numpy import array, hstack
import matplotlib.pyplot as plt
from src import SRC_PATH




def test():
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

    #Setting parameters
    year_length = 200
    r = 0.03
    g = 0.01
    net_gov_wealth = -3217.7e+09
    net_gov_spendings = 0

    simulation.set_population_projection(year_length=year_length, method="exp_growth")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()

    simulation.set_gov_wealth(net_gov_wealth)
    simulation.set_gov_spendings(net_gov_spendings)


    #Calculating net transfers
    #Net_transfers = tax paid to the state minus money recieved from the state
    #TODO: transform this in a method
    simulation.cohorts['total_taxes'] = 0
    simulation.cohorts['total_payments'] = 0
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    
    
    """
    Reproducing the table 2 : Comptes générationnels par âge et sexe (Compte central)
    """
    #Generating generationnal accounts

    simulation.create_present_values(typ = 'net_transfers')
    print "PER CAPITA PV"
    print simulation.percapita_pv.xs(0, level = 'age').head()
    print simulation.percapita_pv.xs((0, 2007), level = ['sex', 'year']).head()


    # Calculating the Intertemporal Public Liability
    ipl = simulation.compute_ipl(typ = 'net_transfers')
    print "------------------------------------"
    print "IPL =", ipl
    print "share of the GDP : ", ipl/8050.6e+09*100, "%"
    print "------------------------------------"
    
    #Calculating the generational imbalance
    gen_imbalance = simulation.compute_gen_imbalance(typ = 'net_transfers')
    print "----------------------------------"
    print "imbalance : [n_1=", gen_imbalance[0], ", n_1-n_0=", gen_imbalance[1], ", n_1/n_0=", gen_imbalance[2],"]"
    print "----------------------------------"    
    
    
    #Creating age classes
    cohorts_age_class = AccountingCohorts(simulation.percapita_pv.create_age_class(step = 5))

    cohorts_age_class._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe = cohorts_age_class.xs((1, 2007), level = ['sex', 'year'])
    age_class_pv_ma = cohorts_age_class.xs((0, 2007), level = ['sex', 'year'])
    print "AGE CLASS PV"

    print age_class_pv_fe.head()
    print age_class_pv_ma.head()
    
    
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

