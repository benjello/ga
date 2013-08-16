# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on 14 mai 2013

@author: Jérôme SANTOUL
'''
from __future__ import division
from pandas import DataFrame, read_csv, concat, ExcelFile, HDFStore
from numpy import NaN, arange, hstack, array
from src.lib.AccountingCohorts import AccountingCohorts
from cohorte import Cohorts

class DataCohorts(Cohorts):
    '''
    Stores data for projection. Data should be a data frame with multindexing and at most one 
    column dimension. This object is meant to contain only original data and perform projection on it.
    Default columns are 'year', set col_names if different.
    Methods of this class allow to fill the object and create accounting_Cohorts objects.
    '''


    def __init__(self, data=None, index=None, columns=None, 
                 dtype=None, copy=False):
        super(DataCohorts, self).__init__(data, index, columns , dtype, copy)

        
    def set_population_from_csv(self, datafile):
        '''
        Sets population from csv file
        '''
        data = read_csv(datafile, index_col = [0,1])
        stacked = data.stack()
        stacked.index.names[2] = 'age'
        stacked = stacked.reorder_levels(['sex', 'year', 'age']).sortlevel()
        self.__init__(data = stacked, columns = ['pop'])
        
        
                
    def _fill(self, df, year = None):
        """
        Takes age, sex profile (per capita transfers) found in df
        to fill year 'year' or all empty years if year is None
        This is a private method.
        Parameters
        ----------
        
        df : DataFrame
             a dataframe containing the profiles
        
        year : int, default None
               if None fill all the years else only the given year
        
        """        
        if not isinstance(df, DataFrame): 
            df = DataFrame(df)

        for col_name in df.columns:
            if col_name not in self._types:
                self.new_type(col_name)
                typ = col_name
                tmp = df[typ]
                tmp = tmp.unstack(level="year")
                tmp = tmp.dropna(axis=1, how="all")
                self._types_years[typ] = tmp.columns
                
            else:
                raise Exception("column already exists")
        
        if year is None:
            df_insert = df.reset_index(level='year', drop=True)
            years = sorted(self.index_sets['year'])
            list_df = [df_insert] * len(years)
            df_tot = concat(list_df, keys = years, names =['year'])
            df_tot = df_tot.reorder_levels(['age','sex','year'], axis=0)
            
        else:
            yr = year
            df_tot = None
            df_insert = df.reset_index()
            df_insert['year'] = yr
            if df_tot is None:
                df_tot = df_insert
            else:
                df_tot.append(df_insert, ignore_index=True)
                df_tot = df_tot.set_index(['age','sex','year'])

        self.update(df_tot)


    def population_project(self, year_length = None, method = None, growth_rate = None):
        """
        Continuation of population to provide convergent present values
        
        Parameters
        ----------
        year_length : int, default None
                      Duration to continue the population projection
        method : str, default None
                 The value must be 'stable' or 'exp_growth'  
        """

        if 'pop' not in self.columns:
            raise Exception('pop is not a column of cohort')
        if year_length is None:
            raise Exception('a duration in years should be provided')
        if method is None:
            raise Exception('a method should be specified')
        years = self.index_sets['year']
        first_year = min(years)
        last_year = max(years)
        
        if ( first_year + year_length ) > last_year:
            new_last_year = first_year + year_length
        else:
            return

        if method == 'stable':
            last_pop = self.xs(last_year, level='year', axis=0)
            pop = DataFrame(self['pop'])
            years = range(last_year+1,new_last_year+1)
            list_df = [last_pop] * len(years)

            pop = concat(list_df, keys = years, names =['year'])
            pop = pop.reorder_levels(['age','sex','year'], axis=0)
            combined = self.combine_first(pop)
            self.__init__(data = combined, columns = ['pop'])
            

        if method == 'exp_growth':
            if growth_rate is None:
                    raise Exception('a growth rate must be provided for the method')
            
            last_pop = self.xs(last_year, level='year', axis=0)
            pop = DataFrame(self['pop'])
            years = range(last_year+1,new_last_year+1)
            list_df = [last_pop] * len(years) 

            pop = concat(list_df, keys = years, names =['year'])
            pop = pop.reorder_levels(['age','sex','year'], axis=0)
            pop = Cohorts(pop)
            pop.gen_grth(growth_rate)
            pop['pop'] *= pop['grth']
            del pop['grth']
            
            combined = self.combine_first(pop)
            self.__init__(data = combined, columns = ['pop'])


    def proj_tax(self, rate = None , discount_rate = None , typ = None, method = None):
        """
        Projects taxes either per_capita or aggregate at the constant growth_rate rate
        
        Parameters
        ----------        
        rate : float,
               Growth rate of the economy
        discount_rate : float
        typ : the type of data which has to be expanded.
            The cohort should have one column for the population and at least one other column (the profile)
            which will be expanded
        method : str
            the method used for the projection 
            the name has to be either 'per_capita' or 'aggregate'
        """
        
        if rate is None:
            raise Exception('no growth_rate provided')
        if discount_rate is None:
            self.proj_tax(rate , 0 , typ, method)
            return
        if method is None:
            raise Exception('a method should be specified')
        if typ is None:
            for typ in self._types:
                self.proj_tax(rate , discount_rate , typ, method)
            return
        if typ not in self.columns:
            raise Exception('this is not a column of cohort')
        else:
            self.gen_grth(rate)
            if method == "per_capita":
                self[typ] = self[typ]*self['grth']
                
            if method == "aggregate":
                typ_years = self._types_years[typ]
                last_typ_year = max(typ_years)         
                last_typ_pop = self.xs(last_typ_year, level='year', axis=0)  
                years = self.index_sets['year']
                last_year = max(years)
                proj_years = range(last_typ_year, last_year+1)
                list_pop_df = [last_typ_pop] * len(proj_years)
                frozen_pop = concat(list_pop_df, keys = years, names =['year'])
                frozen_pop = frozen_pop.reorder_levels(['age','sex','year'], axis=0)
                
                
                self[typ] = self[typ]*self['grth']*frozen_pop["pop"]/self["pop"]
                # print self
            else:
                NotImplementedError

    def compute_net_transfers(self, name = 'net_transfers', taxes_list = [], payments_list = []):
        """
        Creates a new column total_payments in the DataCohorts which combines the profiles.
        
        Parameters
        ----------
        name : str (default net_transfers)
            The name of the computed column
        taxes_list : list
            A list of the name of the columns containing all the taxes profiles
        payments_list : list
            A list of the names of the columns containing all the subsidies and payments profiles
        """

        self.new_type(name)
        self['total_taxes'] = 0
        self['total_payments'] = 0
        for typ in taxes_list:
            if typ not in self._types:
                self._nb_type += 1
                self._types.append(typ)
            self['total_taxes'] += hstack(self[typ])
        
        for typ in payments_list:
                if typ not in self._types:
                    self._nb_type += 1
                    self._types.append(typ)
                self['total_payments'] += hstack(self[typ])
    
        self[name] = self['total_taxes'] - self['total_payments']
        if self[name].all() == 0:
            raise Exception('The computed column contains only zeros')

         
    def aggregate_generation_present_value(self, typ, discount_rate=None):
        """
        Computes the present value of one column for the whole generation
        
        Parameters
        ----------
        typ : str
              Name of the column of the per capita profile of tax or transfer
        discount_rate : float
                        Rate used to calculate the present value
        Returns
        -------
        res : an AccountingCohorts with column 'typ' containing the aggregat present value of typ 
        """
        if typ not in self._types:
            raise Exception('cohort: variable %s is not in self._types' %typ)
            return
        if discount_rate is None:
            discount_rate = 0.0
        if 'dsct' not in self._types:
            self.gen_dsct(discount_rate)
        tmp = self['dsct']*self[typ]*self['pop']
        tmp = tmp.unstack(level = 'year')  # untack year indices to columns
        
        pvm = tmp.xs(0, level='sex')
        pvf = tmp.xs(1, level='sex') #Assuming 1 is the index for females resp. 0 is male.
        
        yr_min = array(list(self.index_sets['year'])).min()
        yr_max = array(list(self.index_sets['year'])).max()
        
        for yr in arange(yr_min, yr_max)[::-1]:
            pvm[yr] += hstack( [ pvm[yr+1].values[1:], 0]  )
            pvf[yr] += hstack( [ pvf[yr+1].values[1:], 0]  )
            
        pieces = [pvm, pvf]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.stack()
        res = res.reset_index()
        res = res.set_index(['age', 'sex', 'year'])
        res.columns = [typ]
        return AccountingCohorts(res)


    def per_capita_generation_present_value(self, typ, discount_rate = None):
        """
        Returns present net value per capita of the data typ 
        
        Parameters
        ----------
        typ : str
              Column name
        discount_rate : float
        
        Returns
        -------
        pv_percapita : an AccountingCohorts with column 'typ' containing the per capita present value of typ 
        
        """

        if typ not in self._types:
            raise Exception('cohort: variable %s is not in self._types' %typ)
        pv_gen = self.aggregate_generation_present_value(typ, discount_rate)
        pop = DataFrame({'pop' : self['pop']})
        pv_percapita = DataFrame(pv_gen[typ]/pop['pop'])
        pv_percapita.columns = [typ]
        return AccountingCohorts(pv_percapita)


if __name__ == '__main__':
    pass
