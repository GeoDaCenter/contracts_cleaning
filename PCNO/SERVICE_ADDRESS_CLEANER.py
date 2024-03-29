import re
from string import digits
import ADDRESS_CLEANER as ac


def address_cleaner(string):
    '''
    Cleans a string based on the peculiarities of the PurpleBinder, West Chi,
    DFSS, and MapsCorps datasets. Returns a string.
    '''

    # Strip off leading and trailing whitespace
    string = string.strip()

    # Strings that will be blocked
    blocked = ['CALL FOR DETAILS','CONFIDENTIAL LOCATION','BASEMENT',
               'CONFIDENTIAL','UNDISCLOSED LOCATION','MULTIPLE LOCATIONS',
               'UNDISCLOSED LOCATION- NORTHSIDE','MULTIPLE LOCATIONS CHICAGO',
               'MULTIPLE LOCATIONS CHICAGO AND SUBURBS','DV SHELTER',
               'EDWARD HEALTH & FITNESS CENTER â€” SEVEN BRIDGES']

    # Standardize different spellings of SAINT LOUIS
    if re.findall(r'ST\.? LOUIS',string):
        string = re.sub(r'ST\.? LOUIS', 'SAINT LOUIS',string)

    # Standardize different spellings of SOUTH
    if re.findall(r' S\.[A-Z]+',string):
        string = re.sub(r' S.',' SOUTH ',string)

    # If the string is in blocked, return the empty string
    for item in blocked:
        if string == item:
            return ''

    # Clean out strings that are labeled as phone numbers
    if string.startswith('PHONE') or string.startswith('OFFICE PHONE'):
        return ''

    # Clean up floor labels
    if string.endswith(' FLOOR') or string.endswith(' FL'):
        string = re.sub(r'[0-9]+(ST|ND|RD|TH) FLOOR$','',string)
        string = re.sub(r'[0-9]+(ST|ND|RD|TH) FL$','',string)
    # If string ends with this substring, trim it off
    elif string.endswith('ADH (MC 345)'):
        string = string[0:-len('ADH (MC 345)')]

    # Replace multiple spaces with a single space; replace'C/O'; replace forward
    # slashes
    string = re.sub(r'\s+',' ',string)
    string = re.sub(r'C/O',' ',string)
    string = re.sub(r'/',' ',string)

    # Replace abbreviated directions with full words
    string = re.sub(r'(\s|^)E\.?(?=\s|$)',' EAST',string)
    string = re.sub(r'(\s|^)W\.?(?=\s|$)',' WEST',string)
    string = re.sub(r'(\s|^)N\.?(?=\s|$)',' NORTH',string)
    string = re.sub(r'(\s|^)S\.?(?=\s|$)',' SOUTH',string)

    # Define a dictionary of characters on which to split (dictionary because of
    # the challenge with raw strings and backslashes)
    split_chars = {',':',',
                   '\(':'(',
                   '\)':')',
                   ' - ':' - ',
                   r'\\':'\\',
                   ':':':'}

   # For every key, value pair in the split_chars dictionary:
    for key, value in split_chars.items():
        # If key is found within string:
        if re.findall(key,string):
            # Call splitter on string with value and clean up the string
            string = splitter(string,value)

    # Hard-coding a weird prefix found on some strings
    string = re.sub(r'^C4\s(\s|[A-Z])+(?=([0-9]+\s))','',string)

    # Clean up encoding issues with O'Hare
    string = re.sub(r'O(.)*HARE (INTERNATIONAL )?AIRPORT$','O\'HARE INTERNATIONAL AIRPORT',string)

    # Hard-coded cleanup for strings that end in the word PHONE
    string = re.sub(r' PHONE$','',string)

    # Hard-coded clean-up for strings ending in an ampersand
    string = string.strip(' &')

    # These addresses are causing irremediable problems; hard-coding to solve
    if string == '4944 AND 4909 WEST HURON':
        #print(string)
        return '4944 WEST HURON'
    if string == '9204 SOUTH COMMERCIAL AVENUE 401&402':
        return '9204 SOUTH COMMERCIAL AVENUE'

    # If the address is supposed to end in a number (like a state/cty/US hwy),
    # return it. Else, run it through the address_cleaner module's cleaner
    if re.findall(r' ROUTE [0-9]+$',string):
        return string
    else:
        return ac.address_cleaner(string)


def splitter(string,char):
    '''
    Splits a string into pieces, keeping the parts that appear to contain a real
    address. Returns a string.
    '''

    # Split the string and declare an empty list where pieces will be appended
    split_list = string.split(char)
    keep = []

    # If the address in the second item is a substring of the address in the
    # first item, AND it's not a valid address, strip it out of the first item
    # and return what's left over
    if len(split_list) == 2:
        a,b = split_list
        if a.startswith(b):
            if not re.findall(r'[0-9]\s[A-Z0-9]+',b):
                return a.lstrip(b)

        # If there's a valid address in each string, return the address from the
        # first string
        elif re.findall(r'[0-9]\s[A-Z0-9]+',a) and re.findall(r'[0-9]\s[A-Z0-9]+',b):
            return a

    # If there's an address or an ampersand in the item, keep it
    for item in split_list:
        item = item.strip()
        if re.findall(r'[0-9]+\s[A-Z0-9]+',item) or re.findall(r'&',item):
            keep.append(item)

    # Join the pieces back together and condense multiple spaces
    string = ' '.join(keep)
    string = re.sub(r'\s+',' ',string)

    return string


def clean_zips(df):
    '''
    Cleans zip codes by trimming off +4s and deleting strings longer than five
    digits. Returns a dataframe.
    '''

    # Shortcut
    zipc = 'ZipCode'

    # Split the string at the hyphen and keep only the first part
    df[zipc] = df[zipc].apply(lambda x: x.split('-')[0])

    # If the zip code isn't five digits, return the empty string
    df[zipc] = df[zipc].apply(lambda x: x if len(x) == 5 else '')

    return df


def full_cleaning(df):
    '''
    Cleans each address field, then combines the two and cleans them together.
    Calls the zip code cleaner. Returns a dataframe.
    '''

    # Call the address cleaner on Address1 and then Address2
    df['Address1'] = df['Address1'].apply(address_cleaner)
    df['Address2'] = df['Address2'].apply(address_cleaner)

    # Concatenate Address1 and Address2 and store in new Address column
    df['Address'] = df.apply(lambda x: x['Address1'] + ',' + x['Address2'],axis=1)

    # Send Address column through the cleaner; splitter will take care of the
    # concatenated values
    df['Address'] = df['Address'].apply(address_cleaner)

    # Drop the original address columns
    df = df.drop(['Address1','Address2'],axis=1)

    # 309 HARRISON STREET	OAK PARK	IL	-87.78231947	41.87261454	60302
    har1 = '309 HARRISON STREET'
    har2 = '309 WEST HARRISON STREET'
    sinn = 'SARAHS INN'

    df['ZipCode'] = df.apply(lambda x: '60304' if x['Address'] == har1 and
                             x['Name'] == sinn else x['ZipCode'], axis=1)
    df['City'] = df.apply(lambda x: 'OAK PARK' if x['Address'] == har1 and
                             x['Name'] == sinn else x['City'], axis=1)

    df['ZipCode'] = df.apply(lambda x: '60304' if x['Address'] == har2 and
                             x['Name'] == sinn else x['ZipCode'], axis=1)
    df['City'] = df.apply(lambda x: 'OAK PARK' if x['Address'] == har2 and
                             x['Name'] == sinn else x['City'], axis=1)

    df['Address'] = df.apply(lambda x: har1 if x['Address'] == har2 and
                             x['Name'] == sinn else x['Address'], axis=1)


    # Clean the zip codes
    df = clean_zips(df)

    return df
