'''
Created on 20 mars 2013

@author: benjello
'''

from pandas import HDFStore
from cohorte import Cohorts

class Simulation(object):
    """
    A simulation object contains all parameters to compute a simulation 
    """
    def __init__(self):
        super(Simulation, self).__init__()
        self.population = None
        self.profiles = None
        self.cohorts = None
        self.population_projection = None
        self.tax_projection = None
        self.growth_rate = None
        self.discount_rate = None
        self.country = None
        
        
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
        
    def create_cohorts(self):
        """
        Create cohorts according to population, tax and transfers,
        and state expenses projection    
        """
        population = self.population
        cohorts = Cohorts(data = population, columns = ['pop'])
        
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

if __name__ == '__main__':
    pass
