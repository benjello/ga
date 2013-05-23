# -*- coding:utf-8 -*-
# Created on 22 mars 2013
# Copyright © 2013 Clément Schaff, Mahdi Ben Jelloul, Jérôme SANTOUL

'''
Created on 14 mai 2013

@author: Jérôme SANTOUL
'''
import nose
from src.lib.DataCohorts import DataCohorts
from numpy import array
from src.scripts.tests.utils import (create_testing_population_dataframe,
                                     create_empty_population_dataframe,
                                     create_constant_profiles_dataframe,
                                     create_neutral_profiles_cohort)


         
def test_population_projection():
    # Create cohorts
    start_data = 2001
    end_data = 2061
    population = create_empty_population_dataframe(start_data, end_data)
    cohorts = DataCohorts(data = population, columns = ['pop'])

    # Complete population projection
    year_length = 100
    end_project = start_data + year_length
    method = 'exp_growth'   
    growth_rate = n = 0.05
    cohorts.population_project(year_length, method = method, growth_rate = n)
    
    year_control = 2082
    control_value = (1+n)**(year_control - end_data - 1)
    test_value = cohorts.get_value((0,0,2081), "pop")
    assert test_value == control_value


def test_fill_cohort():   
    population = create_empty_population_dataframe(2001, 2061)
    profiles = create_constant_profiles_dataframe(population, tax = -1, subsidies = 0.5)
    cohorts_test = DataCohorts(data = population, columns = ['pop'])
    cohorts_test.fill(profiles, year = None)
    test_value = cohorts_test.get_value((0,0,2060), 'tax')
    assert test_value == -1
    
def test_compute_net_transfers():
    population = create_empty_population_dataframe(2001, 2061)
    profiles = create_constant_profiles_dataframe(population, tax = 1, subsidies = 0.5)
    tax = ['tax']
    subsidy = ['subsidies']
    cohorts_test = DataCohorts(data = population, columns = ['pop'])
    cohorts_test.fill(profiles, year = None)
    cohorts_test.compute_net_transfers(taxes_list = tax, payments_list = subsidy)
    test_value = cohorts_test.get_value((0,0,2060), 'net_transfers')
    assert test_value == 0.5
    
    pass

def test_tax_projection():

    population = create_empty_population_dataframe(2001, 2061)
    profile = create_constant_profiles_dataframe(population, tax = -1, sub=0.5) 
    g = 0.05
    r = 0
    cohort = DataCohorts(population)
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
    cohort = DataCohorts(population)
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
              
    cohort3 = cohort2.per_capita_generation_present_value('tax')
    res_control = cohort2.aggregate_generation_present_value('tax', discount_rate=0)
    
    count = 0
    while count <= 100:
#         print cohort3.get_value((count, 1, 2001), 'tax'), res_control.get_value((count, 0, 2001), 'tax')
        assert cohort3.get_value((count, 1, 2001), 'tax')*size_generation == res_control.get_value((count, 0, 2001), 'tax')
        count +=1

if __name__ == "__main__":
    
#     test_population_projection()
#     test_fill_cohort()
#     test_tax_projection()
#     test_tax_projection_aggregated()
#     test_present_value()
    
    nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])

    