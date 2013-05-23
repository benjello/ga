# -*- coding:utf-8 -*-
'''
Created on 14 mai 2013

@author: Jérôme SANTOUL
'''
import nose
from src.lib.DataCohorts import DataCohorts
from src.lib.AccountingCohorts import AccountingCohorts
from numpy import array
from src.scripts.tests.utils import (create_testing_population_dataframe,
                                     create_empty_population_dataframe,
                                     create_constant_profiles_dataframe,
                                     create_neutral_profiles_cohort)



def test_compute_ipl():
    
    size_generation = 3
    cohort2 = create_neutral_profiles_cohort(population = size_generation)
    cohort3 = cohort2.aggregate_generation_present_value('tax')
    ipl = cohort3.compute_ipl(typ = 'tax', net_gov_wealth = 10)
    assert ipl == 10.0
    
    

def test_generation_extraction():
    # Creating a fake cohort
    n = 0.00
    r = 0.00
    g = 0.05
    population = create_testing_population_dataframe(year_start=2001, year_end=2061, rate=n)
    profile = create_constant_profiles_dataframe(population, tax=-1, sub=0.5)
    cohort = DataCohorts(population)
    # Applying projection methods
    year_length = 199
    method = 'stable'   
    cohort.population_project(year_length, method = method)  
    cohort.fill(profile)
    typ = None
    cohort.proj_tax(g, r, typ,  method = 'per_capita')
    cohort = AccountingCohorts(cohort)
    cohort._types = ['tax']
    
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
    profile = create_constant_profiles_dataframe(population, tax = 1.0, sub=-0.5) 

    cohort = DataCohorts(population)
    cohort.fill(profile)
    cohort2 = cohort.per_capita_generation_present_value('tax', discount_rate=0)
    print cohort2.head()
    print cohort2.tail()
    step = 5.0
    age_class = cohort2.create_age_class(step = step)
    print age_class.tail(10)
    count = 0
    while count < 100:
        assert age_class.get_value((count, 1, 2001), 'tax') == 2
        count += step



if __name__ == "__main__":
#     test_compute_ipl()
#     test_create_age_class()
#     test_generation_extraction()
    nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])
