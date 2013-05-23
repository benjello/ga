# -*- coding:utf-8 -*-
# Created on 22 mars 2013
# Copyright © 2013 Clément Schaff, Mahdi Ben Jelloul, Jérôme SANTOUL


# Good docs about nosetest
# http://ivory.idyll.org/articles/nose-intro.html
# https://nose.readthedocs.org/en/latest/testing.html

import nose
from src.lib.cohorte import Cohorts
from numpy import array
from src.scripts.tests.utils import (create_testing_population_dataframe,
                                     create_empty_population_dataframe,
                                     create_constant_profiles_dataframe,
                                     create_neutral_profiles_cohort)
                                     
 


def test_empty_frame_generation():

    year_start = 2001
    year_end = 2061
    population_dataframe = create_empty_population_dataframe(year_start, year_end)
    test_value = population_dataframe.get_value((0,0,2043), "pop")
    assert test_value == 1
         


def test_column_combination():
    year_start = 2001
    pop_dataframe = create_empty_population_dataframe(year_start, 2061)
#     print pop_dataframe
    profiles_dataframe = create_constant_profiles_dataframe(pop_dataframe, tax=-1.0, sub=0.5)
#     print profiles_dataframe
    profiles_dataframe['net'] = profiles_dataframe.sum(axis=1) 
#     print profiles_dataframe['net']
    test_value = profiles_dataframe.get_value((0,0,2001), 'net')
#     print test_value
    assert test_value == -0.5



def test_dsct():
    population = create_empty_population_dataframe(2001, 2061)
    cohorts = Cohorts(data = population, columns = ['pop']) 
    cohorts.gen_dsct(0.05)
    test_value = cohorts.get_value((0,0,2060), 'dsct')
#    print test_value
    assert test_value <= 1
    



def test_filter_value():
    """
    Testing the method to filter data from a given cohort
    """
    #Generate a testing cohort with 5% population and economy growth 
    n = 0.05
    population = create_testing_population_dataframe(year_start=2001, year_end=2061, rate=n)
    profile = create_constant_profiles_dataframe(population, tax=-1, sub=0.5)
    cohort = Cohorts(population)
    cohort.fill(profile)
    r = 0.0
    g = 0.05
    column = None
    cohort.proj_tax(g, r, column,  method = 'per_capita')
    #Testing restrictions
    cohort_filtered = cohort.filter_value(age = list(range(0, 100, 1)), year = list(range(2001, 2060, 5)), typ = 'tax')
    count = 2001
    while count <= 2060:
        assert abs(cohort_filtered.get_value((0, 1, count), 'tax') + (1+g)**(count-2001)) == 0.0
        count +=5



if __name__ == '__main__':

#     test_population_projection()
#     test_dsct() #Working
#     test_empty_frame_generation()
#     test_population_projection()
#     test_column_combination() #Working
#     create_neutral_profiles_cohort()
#     test_filter_value()
#     nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])
#     nose.core.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'], exit=False)