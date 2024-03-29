import numpy as np
import pandas as pd


HQ = '../../../rcc-uchicago/PCNO/CSV/chicago/contracts_w_hq_addresses.csv'
GEO = '../../../rcc-uchicago/PCNO/CSV/chicago/Geocoded Service Addresses/map1_addresses_geocoded.csv'
CATEGORIES = '../../../rcc-uchicago/PCNO/Rule-based classification/chi_cook_il_classified.csv'
MAP1B = '../../../rcc-uchicago/PCNO/CSV/chicago/Maps/map1b.csv'


def read_geo():
    '''
    Reads in the geocoded addresses for map 1. Drops the 'Match Score' column.
    Returns a dataframe.
    '''

    # Read in the geocoded file and convert Zip to string
    df = pd.read_csv(GEO,converters={'Zip':str})

    # Drop these columns
    df = df.drop(['Match Score','AddressID'],axis=1)

    return df


def read_contracts():
    '''
    Reads in the contracts with headquarter addresses. Returns a dataframe.
    '''

    # Read in the contracts with headquarter addresses and convert Zip to string
    df = pd.read_csv(HQ,converters={'Zip':str})

    # Keep only records where the state is IL
    df = df[df['State'] == 'IL']

    return df


def add_jurisdic(df):
    '''
    Takes a dataframe of contracts and adds a column with the jurisdiction of
    each contract, that is, whether it is from City of Chicago, Cook County, or
    State of Illinois. Returns a dataframe.
    '''

    df['Jurisdic'] = ''
    df['Jurisdic'] = df.apply(lambda x: 'CHICAGO' if x['CSDS_Contract_ID'].startswith('CHI') \
                              else 'COOK' if x['CSDS_Contract_ID'].startswith('COOK') \
                              else 'IL', axis=1)

    return df


def read_categories():
    '''
    Reads in the service-code classifications for the contracts. Returns a
    dataframe.
    '''

    # Read in the classifications file
    df = pd.read_csv(CATEGORIES)

    # Keep only these columns
    df = df[['Classification','Contract Number']]

    # Rename column
    df = df.rename(columns={'Contract Number':'ContractNumber'},index=str)

    return df


def merge():
    '''
    Reads in the geocoded headquarter addresses, the contracts, and the service
    classifications. Merges the dataframes together. Returns a dataframe.
    '''

    # Read in the geocoded file
    geo = read_geo()

    # Read in the contracts and add jurisdiction
    contracts = read_contracts()
    contracts = add_jurisdic(contracts)

    # Read in the service categories
    cats = read_categories()

    # Merge the geocoding into the contracts
    df = contracts.merge(geo,how='left')

    # Merge the service categories into the contracts
    df = df.merge(cats,how='left')

    # Drop this column
    df = df.drop('AddressID',axis=1)

    return df.drop_duplicates().reset_index(drop=True)


if __name__ == '__main__':

    merged = merge()
    merged.to_csv(MAP1B,index=False)
