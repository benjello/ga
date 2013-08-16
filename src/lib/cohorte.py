# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on May 22, 2012

@author: Clément Schaff, Mahdi Ben Jelloul
'''

from __future__ import division
from pandas import DataFrame, read_csv, concat, ExcelFile, HDFStore
from numpy import NaN, arange, hstack, array
import os

class Cohorts(DataFrame):
    """
    Stores data for some cohortes. Data should be a data frame with multindexing and at most one 
    column dimension. 
    Default columns are 'year', set col_names if different.
    """
    def __init__(self, data=None, index=None, columns=None, 
                 dtype=None, copy=False):
        super(Cohorts, self).__init__(data, index, columns , dtype, copy)

        if data is not None:
            if set(['age', 'sex', 'year']) != set(self.index.names):
                raise Exception('Need  age, sex and year indexes')

            self.index_sets = dict()
            self._begin = None
            self._end   = None
            self._agemin = None
            self._agemax = None
            self._agg = None
            self._nb_type = 0
            self._types = list()
            self._types_years = dict()   # TODO: merge this dict with the previous list

            self._year_min = None
            self._year_max = None
            
            self.post_init()


    def post_init(self):
        """
        Post initialization, computes index_sets, _agemin, _agemax attributes
        """
        temp = zip(*self.index)
        name = self.index.names 
        for t, n in zip(temp, name):
            self.index_sets[n] = set(t)

        self._agemin = min(self.index_sets['age'])
        self._agemax = max(self.index_sets['age'])
        self._year_min = min(self.index_sets['year'])
        self._year_max = max(self.index_sets['year'])


    def totaux(self, by, column, pivot = False):
        """
        Compute a pivot table 
        
        Parameters
        ----------
        by : str
             Variable which values are kept constant in each group (by variable)
        column : str
                 Variable which is summed by group 
        pivot : boolean, default False
                if True returns a pivot_table
        
        Returns
        -------
        df : a Dataframe
        
        """
        if pivot:
            # should return a square DataFrame where the last level is used as columns
            if len(by) ==2 and isinstance(by, list):
                a = self[column]
                a = a.groupby(level = by).sum()
                return a.unstack()
        df = DataFrame({column : self[column].groupby(level = by).sum()})
        return df 
            
    
    def new_type(self, name ):
        """
        Creates a new empty column
        
        Parameters
        ----------
        
        name : str
               Name of the new empty column
        """
        if name not in self._types:
            self[name] = NaN
            self._nb_type += 1
            self._types.append(name)
        else:
            raise Exception('%s already exists'% name)

    def fill_old(self, df, year = None):
        """
        Takes an age, sex profile (per capita transfers) in df 
        to fill year 'year' or all years if year is None
        """
        if isinstance(df, DataFrame):
            df1  = df 
        else:
            df1 = DataFrame(df)

        for col_name in df1.columns:
            if col_name not in self._types:
                self.new_type(col_name)

        if year is None:
            for yr in sorted(self.index_sets['year']):
                self.fill(df, year = yr)
        else:
            yr = year
            if isinstance(df, DataFrame):
                df1  = df 
            else:
                df1 = DataFrame(df)
            
            for col_name, column in df1.iteritems():
                column = column.reset_index()
                column['year'] = yr
                column = column.set_index(['age','sex','year'])
                self.update(column)
        
    def add_agg(self, agg):
        '''
        Stores aggregates in Cohorte  TODO: REMOVEME DEPRECATED
        '''
        self._agg = agg*1e9

    def to_percap(self):
        '''
        Re-scale profiles to per capita amounts of transfers (after projection if it occurred)
        using aggregates
        '''
        
        if self._agg is None:
            raise Exception('cohorte: exiting to_perrcap because self._agg is None')
            return
        
        for typ in range(1, self._nb_type+1):
            var = 'typ%i'%typ
            self['tmp'] = self[var]*self['pop']
            sums = self.totaux(by = 'year', column = 'tmp')
            
            unities = self._agg['%i' %typ]/sums
            # warning: creates NaN from 2071 to 2200 because agg unknown
            
            grouped = self.groupby(level = ['sex', 'age'])[var]
            self[var] = grouped.transform(lambda x: x*unities.values)
        
            yr_min = min(self.index_sets['year'])
            for yr in range(yr_min,2201):   # TODO check yr -1 ?? 
                a = self.xs(yr-1, level='year', axis=0)[var]
                self.xs(yr, level='year', axis=0)[var] = a

    
    def gen_grth(self, g):
        self._growth_rate = g
        self['grth'] = NaN
        grouped = self.groupby(level = ['sex', 'age'])['grth']
        nb_years = len(self.index_sets['year'])
        self['grth'] = grouped.transform(lambda x: (1+g)**(arange(nb_years)))

    def gen_dsct(self, r):
        self._discount_rate = r 
        self['dsct'] = NaN
        grouped = self.groupby(level = ['sex', 'age'])['dsct']
        nb_years = len(self.index_sets['year'])
        self['dsct'] = grouped.transform(lambda x: 1/((1+r)**arange(nb_years)))
    
    def gen_actualization(self, arg1 , arg2):
        """
        A method to generate a column of actualization coefficients to be used with profiles data
        
        Parameters
        ----------
        arg1 : any growth rate 
        arg2 : any discount rate (such as interest rate)
        """
        self['actualization']= NaN
        grouped = self.groupby(level = ['sex', 'age'])['actualization']
        nb_years = len(self.index_sets['year'])
        self['actualization'] = grouped.transform(lambda x: ((1+ arg1)/(1+ arg2)**arange(nb_years)))        

    def filter_value(self, age=None, sex=None, year=None, typ=None):
        """
        A method to filter a multi-index Cohort in an easy fashion.
        
        Parameters
        ----------
        age : List
            The values of the age index have to be between 0 and 100 included
        sex : 0 or 1
            The sex index we are interested in. 0 stands for males and 1 for females. Default is both.
        year : List
            The years we are interested in.
        typ : Str
            The data we want to select
            
        Returns
        -------
        A cohort with the specified index and columns
        """
        #Setting up defaults arguments if not given
        if typ is None:
            typ = self._types
        #Setting up filter to check if the arguments are valid
#         if typ not in self._types:
#             raise Exception('This is not a valid column of the cohort')
        #Setting up filters
        if age is not None:
            filter_age = array([x in age for x in self.index.get_level_values(0)])
        if sex is not None:
            filter_sex = array(self.index.get_level_values(1) == sex)     
        if year is not None:
            filter_year = array([x in year for x in self.index.get_level_values(2)])
        
        #Filtering the cohort
        if age is None:
            if sex is None:
                if year is None:
                    restricted_cohort = self.loc[:, typ]  
#                     return restricted_cohort
                else:
                    restricted_cohort = self.loc[filter_year, typ]
#                     return restricted_cohort
            else:
                if year is None:
                    restricted_cohort = self.loc[filter_sex, typ]
#                     return restricted_cohort
                else:
                    filter_SY = array(filter_sex & filter_year)
                    restricted_cohort = self.loc[filter_SY, typ]
#                     return restricted_cohort
        else:
            if sex is None:
                if year is None:
                    restricted_cohort = self.loc[filter_age, typ]  
#                     return restricted_cohort
                else:
                    filter_AY = array(filter_age & filter_year)
                    restricted_cohort = self.loc[filter_AY, typ]
#                     return restricted_cohort
            else:
                if year is None:
                    filter_AS = array(filter_age & filter_sex)
                    restricted_cohort = self.loc[filter_AS, typ]
#                     return restricted_cohort
                else:
                    filter3 = array(filter_age & filter_sex & filter_year)
#                     print filter3
                    restricted_cohort = self.loc[ filter3, typ]
#                     return restricted_cohort
        restricted_cohort_ = Cohorts(restricted_cohort)
        restricted_cohort_.columns = [typ]
        return restricted_cohort_


    def get_unknown_years(self, typ):
        """
        
        """
        cohorts_years = range(self._first_year, self._last_year+1)
        
        profile = self._profiles_years[typ]
        
        

if __name__ == '__main__':
    pass