# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on 14 mai 2013

@author: Jérôme SANTOUL
'''
from __future__ import division
from pandas import concat
from numpy import array
from cohorte import Cohorts

class AccountingCohorts(Cohorts):
    '''
    Stores computed net transfers obtained with data from data_Cohorts. Data should be a data frame with multindexing and at most one 
    column dimension. These cohorts should only contain national accounting data.
    Default columns are 'year', set col_names if different.
    Methods of this class allow index computation for national accounting.
    '''


    def __init__(self, data=None, index=None, columns=None, 
                 dtype=None, copy=False):
        super(AccountingCohorts, self).__init__(data, index, columns , dtype, copy)
     
    def extract_generation(self, year, typ, age = None):
        """
        Returns a dataframe containning chosen data to follow the evolution of a given group over time.
         
        Parameters
        ----------
        year : Int
                A year of reference contained in the cohort.
        typ : Str
              A column or a list of columns of the cohort that one wants to follow
        age : Int
              Default is zero. The age of reference of the group one is interested in.
         
        Returns
        -------
        generation_cohort : a cohort dataframe with the data of the group of people 
                            whose given references belong to. 
        """      
 
        if year is None:
            raise Exception('a year of reference is needed')
        if year not in list(self.index_sets['year']):
            raise Exception('The given year is not valid')
        year_min = array(list(self.index_sets['year'])).min()
        year_max = array(list(self.index_sets['year'])).max()
        if typ not in self._types:
            raise Exception('the given column is not in the cohort')
         
        #Normalizing the age if not given
        if age is None:
            age = 0
                 
        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
         
        #Creating lower bounds for the filter generation
        if age > 0:
            if year-age >= year_min:
                start_age = 0
                year_start = year - age
            else:
                start_age = age - (year - year_min)
                year_start = year_min
        else:
            start_age = age
            year_start = year
 
        #Creating upper bounds for filter_list
        if year + (100-age) >= year_max:
            year_end = year_max
            end_age = age + (year_max - year)
        else:
            year_end = year + 100 - age
            end_age = 100
 
        #Creating the filtering list
        filter_list = zip(range(start_age, end_age+1), range(year_start, year_end+1))
         
#         Generation the generation DataFrame
        generation_data_male = pvm.loc[filter_list, typ]
        generation_data_female = pvf.loc[filter_list, typ]
          
        pieces = [generation_data_male, generation_data_female]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reorder_levels(['age','sex','year'])
          
        generation_cohort = Cohorts(res)
        generation_cohort.columns = [typ]
        return generation_cohort
 
 
    
    def create_age_class(self, step = 1, typ = None):
        """
        Transform a filled cohort dataframe by regrouping 
        age indexies in age class indexies. The size of the age class is indicated by the step argument
         
        Parameters
        ----------
        step : Int
        The number of years included in the age class
         
        Returns
        -------
        res : A DataFrame of the Cohorts class with age indexes replaced with class indicies
        """
        
        if typ is None:
            typ = self._types
        
        # Separating Men and Women
        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
        pvm.reset_index(inplace = True)
        pvf.reset_index(inplace = True)
         
        #Transforming the age indexes
        serie = array(pvm.age)
        pvm['age'] = array((serie//step)*step)
        pvf['age'] = array((serie//step)*step)
        
#         #Old version of age class creation using the simulation.percapita_pv
#         age_class_pvm = pvm.groupby(['age', 'year']).mean()
#         age_class_pvf = pvf.groupby(['age', 'year']).mean() 

       
        #New version which takes in account the change of population over the years        
        age_class_pvm = pvm.groupby(['age', 'year']).sum()
        age_class_pvf = pvf.groupby(['age', 'year']).sum()
        
        age_class_pvm[typ] *= 1/age_class_pvm['pop']
        age_class_pvf[typ] *= 1/age_class_pvf['pop']
         
        #Put back the dataframes together
        pieces = [age_class_pvm, age_class_pvf]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reset_index()
        res = res.set_index(['age', 'sex', 'year'])
        return res            
 
    def compute_ipl(self, typ, net_gov_wealth = None, net_gov_spendings = None):
        """
        Return a value of the intertemporal public liability. 
        The dataframe has to contain the aggregated present values of transfer in order 
        for the method to work correctly
         
        Parameters
        ----------
        typ : the column containing the data used in the calculation
         
        net_gov_wealth : the present value of the wealth of the government
         
        net_gov_spendings : the present value of unventilated
         
        Returns
        -------
         
        ipl : float
            the value of the intertemporal public liability
        """
        if net_gov_wealth is None:
            net_gov_wealth = 0
        if net_gov_spendings is None:
            net_gov_spendings = 0
         
        year_min = array(list(self.index_sets['year'])).min()
        year_max = array(list(self.index_sets['year'])).max()
#         age_min = array(list(self.index_sets['age'])).min()
        age_max = array(list(self.index_sets['age'])).max()
         
        past_gen_dataframe = self.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
 
         
        future_gen_dataframe = self.xs(0, level = 'age')
        future_gen_dataframe = future_gen_dataframe.cumsum()
        future_gen_transfer = future_gen_dataframe.get_value((1, year_max), typ)
        #Note : do not forget to eliminate values counted twice
        ipl = past_gen_transfer + future_gen_transfer + net_gov_wealth - net_gov_spendings - past_gen_dataframe.get_value((0, 0), typ)
        return ipl
     

if __name__ == '__main__':
    pass
