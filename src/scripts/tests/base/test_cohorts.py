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
         
#===============================================================================
# Some tests of the object Cohorts
#===============================================================================

def test_population_projection():
    # Create cohorts
    population = create_empty_population_dataframe(2001, 2061)
    cohorts = Cohorts(data = population, columns = ['pop'])

    # Complete population projection
    year_length = 200
    method = 'stable'   
    cohorts.population_project(year_length, method = method)
    test_value = cohorts.get_value((0,0,2161), "pop")
#    print test_value
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


def test_fill_cohort():   
    population = create_empty_population_dataframe(2001, 2061)
    profiles = create_constant_profiles_dataframe(population, tax = -1, subsidies = 0.5)
    cohorts_test = Cohorts(data = population, columns = ['pop'])
    cohorts_test.fill(profiles, year = None)
    test_value = cohorts_test.get_value((0,0,2060), 'tax')
    print test_value
    assert test_value == -1


def test_dsct():
    population = create_empty_population_dataframe(2001, 2061)
    cohorts = Cohorts(data = population, columns = ['pop']) 
    cohorts.gen_dsct(0.05)
    test_value = cohorts.get_value((0,0,2060), 'dsct')
#    print test_value
    assert test_value <= 1
    
def test_tax_projection():

    population = create_empty_population_dataframe(2001, 2061)
    profile = create_constant_profiles_dataframe(population, tax = -1, sub=0.5) 
    g = 0.05
    r = 0
    cohort = Cohorts(population)
    year_length = 200
    method = 'stable'   
    cohort.population_project(year_length, method = method)
    cohort.fill(profile)
    typ = None
    cohort.proj_tax(g, r, typ,  method = 'per_capita')
#    print cohort
    test_value = cohort.get_value((0,1,2002), 'tax')
    test_value2 = cohort.get_value((0,1,2002), 'sub')
#    print test_value, test_value2
    # TODO: I don't understand the following <- Just wanted to check if the for loop works by changing the value of typ in the test
    assert test_value2 > 0.5 and test_value < -1

    
def test_tax_projection_aggregated():
    n = 1
    population = create_testing_population_dataframe(year_start=2001, year_end=2061, rate=n)
    profile = create_constant_profiles_dataframe(population, tax=-1, sub=0.5)
    g = 0.5
    r = 0.0 
    cohort = Cohorts(population)
    cohort.fill(profile)
    typ = None
    cohort.proj_tax(g, r, typ,  method = 'aggregate')
    test_value = cohort.get_value((0,1,2002), 'tax')
    test_value2 = cohort.get_value((0,1,2002), 'sub')
    assert test_value2 < 0.5 and test_value > -1




def test_present_value():
    """
    Testing all the methods to generate a present value of net transfers
    """
    size_generation = 3
    cohort = create_neutral_profiles_cohort(population = 1)
    cohort2 = create_neutral_profiles_cohort(population = size_generation)

    res = cohort.aggregate_generation_present_value('tax')  
    
#     defining a function which creates the theoretical result of the present value for the following test
    def control_value(x):
        control_value = (50 - abs(x-50))
        return control_value
    
    age = 0
    while age <= 100:
        assert res.get_value((age, 1, 2002), 'tax') == control_value(age), res.get_value((age, 1, 2060), 'tax') == control_value(age)
        age +=1
              
    res_percapita = cohort2.per_capita_generation_present_value('tax')
    res_control = cohort2.aggregate_generation_present_value('tax', discount_rate=0)
    
    count = 0
    while count <= 100:
        print res_percapita.get_value((count, 1, 2001), 'tax'), res_control.get_value((count, 0, 2001), 'tax')
        assert res_percapita.get_value((count, 1, 2001), 'tax')*size_generation == res_control.get_value((count, 0, 2001), 'tax')
        count +=1

def test_compute_ipl():
    
    size_generation = 3
    cohort2 = create_neutral_profiles_cohort(population = size_generation)
    cohort_percapita = Cohorts(cohort2.per_capita_generation_present_value('tax'))
    ipl = cohort_percapita.compute_ipl(typ = 'tax', net_gov_wealth = 10)
    assert ipl == -10.0


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

def test_generation_extraction():
    # Creating a fake cohort
    n = 0.00
    r = 0.00
    g = 0.05
    population = create_testing_population_dataframe(year_start=2001, year_end=2061, rate=n)
    profile = create_constant_profiles_dataframe(population, tax=-1, sub=0.5)
    cohort = Cohorts(population)
    # Applying projection methods
    year_length = 199
    method = 'stable'   
    cohort.population_project(year_length, method = method)  
    cohort.fill(profile)
    typ = None
    cohort.proj_tax(g, r, typ,  method = 'per_capita')
    
    #Extracting generations
    start = 2030
    age = 0
    generation = cohort.extract_generation(start, typ = 'tax', age = age)
    count = age
    while count <= 100 & start + count <= array(list(generation.index_sets['year'])).max():
        assert abs((1+g)**(count+(start-2001)) + generation.get_value((count, 1, start+count), 'tax')) == 0.0
        count +=1

def test_create_age_class():
    """
    Testing the method to regroup age classes
    """
    population = create_testing_population_dataframe(2001, 2003)
    profile = create_constant_profiles_dataframe(population, tax = -1.0, sub=0.5) 

    cohort = Cohorts(population)
    cohort.fill(profile)
    step = 5.0
    age_class = cohort.create_age_class(step = step)
    count = 0
    while count < 100:
        assert age_class.get_value((count, 1, 2001), 'sub') == step/2
        count += step



if __name__ == '__main__':

#     test_population_projection()
#     test_tax_projection() #Now working flawlessly
#     test_tax_projection_aggregated() #Good to go
#     test_fill_cohort() #Working
#     test_dsct() #Working
#     test_empty_frame_generation()
#     test_population_projection()
#     test_column_combination() #Working
#     create_neutral_profiles_cohort()
#     test_present_value()
#     test_filter_value()
#     test_generation_extraction()
#     test_create_age_class()
    test_compute_ipl()

#     nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])
#     nose.core.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'], exit=False)
