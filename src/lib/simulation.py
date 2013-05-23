# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on 20 mars 2013

@author: benjelloul, santoul
'''
from __future__ import division
from pandas import HDFStore
from DataCohorts import DataCohorts
from AccountingCohorts import AccountingCohorts
from numpy import array
from pandas import concat


class Simulation(object):
    """
    A simulation object contains all parameters to compute a simulation 
    """
    def __init__(self):
        super(Simulation, self).__init__()
        self.population = None
        self.profiles = None
        self.population_projection = None
        self.tax_projection = None
        self.growth_rate = None
        self.discount_rate = None
        self.country = None
        self.net_gov_wealth = 0
        self.net_gov_spendings = 0
        self.cohorts = None #A DataCohorts object
        self.aggregate_pv = None #An AccountingCohorts object
        self.percapita_pv = None #An AccountingCohorts object
        
#===============================================================================
# Set of methods to enter various parameters of the simulation object
#===============================================================================
        
    def set_country(self, country):
        """
        Set simulation country
        
        Parameters
        ----------
        country : str
                  country of the simulation
        """
        self.country = country
        
        
    def get_population_choices(self, filename):
        store_pop = HDFStore(filename,'r')
        choices = store_pop.keys()
        store_pop.close()
        return choices
        
    def set_population(self, dataframe):
        """
        Set population dataframe
        
        Parameters
        ----------
        dataframe : pandas DataFrame
                    Dataframe conaining the population
        
        """
        self.population = dataframe 
        
    
    def load_population(self, population_filename, population_scenario):
        """
        Load population form a hdf5 file
        
        Parameters
        ----------
        
        population_filename : str
                   complete path to the hdf5 file
                   
        popualtion_scenario : str
                          name of the table in the hdf5 file
        """
        store_pop = HDFStore(population_filename,'r')
        dataframe = store_pop[population_scenario]
        self.set_population(dataframe)
        store_pop.close()


    def set_profiles(self, dataframe):
        """
        Set profiles dataframe
        
        dataframe : pandas DataFrame
                    Dataframe conaining the profiles
        
        """
        self.profiles = dataframe
    
    def set_gov_spendings(self, G):
        """
        Set the value of unventilated spendings of the government
        
        G : Number
        """
        self.net_gov_spendings = G
    
    def set_gov_wealth(self, W):
        """
        Set the present value of the net government wealth
        """
        self.net_gov_wealth = W
    

    def set_discount_rate(self, r=0):
        """
        Set discount rate
        
        Parameters
        ----------
        
        r : float, default set to 0
            The discount rate
        
        """
        self.discount_rate = r
        
        
    def set_growth_rate(self, g=0):
        """
        Set discount rate
        
        Parameters
        ----------
        
        r : float, default set to 0
            The growth rate
        """
        self.growth_rate = g

    def set_population_projection(self, **kwargs):
        """
        Set population projection parameters
        
        Parameters
        ----------
        
        method : str
                 method use to project population
        """
        if self.population_projection is None:
            self.population_projection = dict()
        for key, value in kwargs.iteritems():
            self.population_projection[key] = value


    def set_tax_projection(self, **kwargs):
        """
        Set tax projection parameters
        
        Parameters
        ----------
        
        method : str
                 method use to project taxes
        """
        if self.tax_projection is None:
            self.tax_projection = dict()
        
        for key, value in kwargs.iteritems():
            self.tax_projection[key] = value


    def load_profiles(self, profiles_filename, profiles_name = "profiles"):
        """
        Load profiles form a hdf5 file
        
        Parameters
        ----------
        
        profiles_filename : str
                   complete path to the hdf5 file
                   
        profiles : str, default to "profiles"
                   name of the table in the hdf5 file
        """
        
        store = HDFStore(profiles_filename, 'r')
        dataframe = store['profiles']
        self.set_profiles(dataframe)

#===============================================================================
# Set of methods to perform the simulation itself
#===============================================================================


    def create_cohorts(self):
        """
        Create cohorts according to population, tax and transfers,
        and state expenses projection    
        """
        population = self.population
        cohorts = DataCohorts(data = population, columns = ['pop'])
        
        # Complete population projection
        year_length = self.population_projection["year_length"]
        method = self.population_projection["method"]        
        cohorts.population_project(year_length, method = method)
        
        # Generate discount factor and growth factor
        cohorts.gen_dsct(self.discount_rate)
        cohorts.gen_grth(self.growth_rate)

        # Fill profiles
        cohorts.fill(self.profiles)
        method = self.tax_projection["method"]
        rate = self.tax_projection["rate"]
        cohorts.proj_tax(rate=rate, method=method)

        # Project net taxes TOOD: see MainWindow widget
        self.cohorts = cohorts
        
    
    def create_present_values(self, typ):
        """
        Create aggregated and per capita present values of net transfers according to the given cohort
        and state expenses projection 
        """
        self.aggregate_pv = self.cohorts.aggregate_generation_present_value(typ, discount_rate = self.discount_rate)
        self.percapita_pv = self.cohorts.per_capita_generation_present_value(typ, discount_rate = self.discount_rate)
        
    def compute_ipl(self, typ):
        """
        Returns the IPL induced by the simulation
        """
        IPL = self.aggregate_pv.compute_ipl(typ, net_gov_wealth = self.net_gov_wealth, net_gov_spendings = self.net_gov_spendings)
        return IPL

        
    def compute_gen_imbalance(self, typ):
        """
        Returns a list of indexes of the generationnal imbalance between the newborn of the reference year 
        and the unborn of the next year.
         
        Returns
        -------
        TODO: finish the doc
         
        """        
        year_min = self.aggregate_pv._year_min
        year_max = self.aggregate_pv._year_max
#         age_min = self.aggregate_pv._agemin
        age_max = self.aggregate_pv._agemax
         
        #Calculating the past transfers for both genders then deducting the equilibrium future transfers
         
        past_gen_dataframe = self.aggregate_pv.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
         
        future_gen_transfer = self.net_gov_spendings - self.net_gov_wealth - past_gen_transfer
          
        #Computing the number of people of the unborn generation
        population_unborn_ma = self.cohorts.get_value((0,0, year_min+1), 'pop')
        population_unborn_fe = self.cohorts.get_value((0,1,year_min+1), 'pop')
        population_unborn = population_unborn_ma + population_unborn_fe
         
        #Reorganizing data to prepare the computation of mu_1
        population_dataframe = self.cohorts.filter_value(age = [0], year = range(year_min+1, year_max+1), typ='pop')
        population_dataframe.gen_actualization(self.growth_rate, self.discount_rate)
        population_dataframe = population_dataframe.unstack(level='sex')
        del population_dataframe[('actualization', 1)] #TODO : check if this line is necessary
        population_dataframe['unborn'] = population_unborn
        population_dataframe['mixed'] = population_dataframe[('pop', 0)] + population_dataframe[('pop', 1)]
        population_dataframe[('actualization', 0)] *= population_dataframe['mixed']/population_dataframe['unborn']
 
        #Computing the coefficient mu_1
        population_dataframe = population_dataframe.cumsum()        
        mu_1 = population_dataframe.get_value((0,year_max), ('actualization', 0))
          
        #Computing the final imbalance coefficients
        population_unborn = population_unborn_ma + population_unborn_fe
        n_1 = future_gen_transfer/(mu_1*population_unborn) # = percapita_future_gen_transfer
        n_0 = (self.percapita_pv.get_value((0, 0, year_min), typ)/2 + 
                               self.percapita_pv.get_value((0, 1, year_min), typ)/2) # = actual_gen_transfer
        imbalance = n_1 - n_0
        imbalance_ratio = n_1/n_0
        coefficients = [n_1, imbalance, imbalance_ratio]
        return coefficients

 

if __name__ == '__main__':
    pass
