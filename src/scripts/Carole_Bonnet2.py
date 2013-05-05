# -*- coding:utf-8 -*-
# Created on 6 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

import os
from src.lib.simulation import Simulation
from src import SRC_PATH


def test():
    
    country = "france"    
    population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
    profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','profiles.h5')
    
    simulation = Simulation()
    print simulation.get_population_choices(population_filename)
        
    population_scenario = "projpop0760_FECcentESPcentMIGcent"
        
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    
    r = 0.0
    g = 0.01
    simulation.set_discount_rate(r)
    simulation.set_growth_rate(g)
    
    #Setting parameters
    year_length = 100
    
    simulation.set_population_projection(year_length=year_length, method="exp_growth")
    simulation.set_tax_projection(method="per_capita", rate=0)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()
    print simulation.cohorts.head()
    
if __name__ == '__main__':
    test()


