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
                
    def fill(self, df, year = None):
        """
        Takes age, sex profile (per capita transfers) found in df
        to fill year 'year' or all years if year is None
        
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
        res : a dataframe with column 'typ' containing the aggregat present value of typ 
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
        # TODO use a loop <- Whatfor ?
#        for sex in self.index_sets[sex]:
        
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
        return res


    def per_capita_generation_present_value(self, typ, discount_rate = None):
        """
        Returns present net value for typ per capita
        
        Parameters
        ----------
        typ : str
              Column name
        
        """

        if typ not in self._types:
            raise Exception('cohort: variable %s is not in self._types' %typ)
        pv_gen = self.aggregate_generation_present_value(typ, discount_rate)
        pop = DataFrame({'pop' : self['pop']})
        pv_percapita = DataFrame(pv_gen[typ]/pop['pop'])
        pv_percapita.columns = [typ]
        return pv_percapita

    def population_project(self, year_length = None, method = None):
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
#             TODO : finish this projection method. Add an argument, add checkpoint if growth rate is None
#             find efficient way to do the growth operation
            last_pop = self.xs(last_year, level='year', axis=0)
            pop = DataFrame(self['pop'])
            years = range(last_year+1,new_last_year+1)
#             self['dsct'] = grouped.transform(lambda x: 1/((1+r)**arange(nb_years)))
            list_df = [last_pop] * len(years) 

            pop = concat(list_df, keys = years, names =['year'])
            pop = pop.reorder_levels(['age','sex','year'], axis=0)
            combined = self.combine_first(pop)
            self.__init__(data = combined, columns = ['pop'])
            pass

    
    def set_population_from_csv(self, datafile):
        '''
        Sets population from csv file
        '''
        data = read_csv(datafile, index_col = [0,1])
        stacked = data.stack()
        stacked.index.names[2] = 'age'
        stacked = stacked.reorder_levels(['sex', 'year', 'age']).sortlevel()
        self.__init__(data = stacked, columns = ['pop'])

    def filter_value(self, age=None, sex=None, year=None, typ=None):
        """
        A method to filter a multi-index Cohort in an easy fashion.
        
        Parameters
        ----------
        age = List
            The values of the age index have to be between 0 and 100 included
        sex = 0 or 1
            The sex index we are interested in. 0 santds for males and 1 for females. Default is both.
        year = List
            The years we are interested in.
        typ = Str
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
        
#         Generation the generation FataFrame
        generation_data_male = pvm.loc[filter_list, typ]
        generation_data_female = pvf.loc[filter_list, typ]
         
        pieces = [generation_data_male, generation_data_female]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reorder_levels(['age','sex','year'])
         
        generation_cohort = Cohorts(res)
        generation_cohort.columns = [typ]
        return generation_cohort


   
    def create_age_class(self, step = 1):
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
        # Separating Men and Women
        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
        pvm.reset_index(inplace = True)
        pvf.reset_index(inplace = True)
        
        #Transforming the age indexes
        serie = array(pvm.age)
        pvm['age'] = array((serie//step)*step)
        pvf['age'] = array((serie//step)*step)
            
        age_class_pvm = pvm.groupby(['age', 'year']).mean()
        age_class_pvf = pvf.groupby(['age', 'year']).mean()
        
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
        
        net_gov_spendings : the present value of unventilated (TODO: check spelling) government's spendings
        
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
        ipl = past_gen_transfer + future_gen_transfer + net_gov_wealth - net_gov_spendings - past_gen_dataframe.get_value((0, 1), typ)
        return ipl
    
    
    
    def get_unknown_years(self, typ):
        """
        
        """
        cohorts_years = range(self._first_year, self._last_year+1)
        
        profile = self._profiles_years[typ]
        
        

if __name__ == '__main__':
    pass