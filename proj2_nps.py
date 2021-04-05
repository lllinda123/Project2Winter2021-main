#################################
##### Name:Lin Li
##### Uniqname: lllinda
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets
import time


class NationalSite:
    """a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    """

    def __init__(self, category, name, address, zipcode, phone, url=None):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone.strip('\n')
        self.url = url

    def info(self):
        return self.name + ' (' + self.category+'): ' + self.address + ' ' + self.zipcode


URL = 'https://www.nps.gov/index.htm'
CACHE_FILE_NAME = 'proj2.json'
CACHE_DICT = {}


def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    if url in cache.keys():  # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]



def build_state_url_dict():
    """ Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    """
    state_dict = {}
    base_url = 'https://www.nps.gov'
    state_url = base_url + '/index.htm'
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    state_parent = soup.find('ul', class_="dropdown-menu SearchBar-keywordSearch")
    state_ls = state_parent.find_all('li', recursive=False)
    for state in state_ls:
        state_link_tag = state.find('a')
        state_path = state_link_tag['href']
        state_url = base_url+state_path
        state_name = state.get_text().lower()
        state_dict[state_name] = state_url

    return state_dict

       

def get_site_instance(site_url):
    """Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    """
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(site_url, CACHE_DICT)
    park_soup = BeautifulSoup(url_text, 'html.parser')
    park_parent = park_soup.find('div', class_='Hero-titleContainer clearfix')
    park_name = park_parent.find('a', class_='Hero-title').get_text()
    try:
        park_category = park_parent.find('div', class_='Hero-designationContainer').find('span', class_='Hero-designation').get_text().strip()
        if park_category == '':
            park_category = 'Not found category'
    except:
        park_category = 'Not found category'

    park_footer_parent = park_soup.find('div', class_='ParkFooter')
    try:
        park_zip_code = park_footer_parent.find('p', class_='adr').find('span', class_='postal-code').get_text().strip()
    except:
        park_zip_code = 'Not found zipcode'
    try:
        park_address = park_footer_parent.find('p', class_='adr').find('span', itemprop='addressLocality').get_text() + \
                       ', ' + park_footer_parent.find('p', class_='adr').find('span', itemprop='addressRegion').get_text()
    except:
        park_address = 'Not found address'
    try:
        park_phone = park_footer_parent.find('span', class_='tel').get_text()
    except:
        park_phone = 'Not found phone number'

    park_instance = NationalSite(park_category, park_name, park_address, park_zip_code, park_phone)

    return park_instance


def get_sites_for_state(state_url):
    """Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    """
    base_url = 'https://www.nps.gov'
    sites_instance_list = []
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(state_url, CACHE_DICT)
    site_soup = BeautifulSoup(url_text, 'html.parser')
    park_parent = site_soup.find('div', id="parkListResults")
    park_name_ls = park_parent.find_all('h3')
    for park_name in park_name_ls:
        park_tag = park_name.find('a')
        park_name = park_tag.get_text()
        park_path = park_tag['href']
        park_url = base_url + park_path + 'index.htm'

        p_instance = get_site_instance(park_url)
        park_address = p_instance.address
        park_category = p_instance.category
        park_zip_code = p_instance.zipcode
        park_phone = p_instance.phone
        site_instance = NationalSite(park_category, park_name, park_address, park_zip_code, park_phone, park_url)
        sites_instance_list.append(site_instance)

    return sites_instance_list


MAP_KEY = secrets.API_KEY


def make_request_with_cache_api(base_url, site_object):
    """Check the cache for a saved result for this base_url+params:values
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.


    Parameters
    ----------
    base_url: string
        The URL for the API endpoint

    site_object: a site instance


    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    """
    cache_file = load_cache()
    params = {'key': MAP_KEY, 'origin': site_object.zipcode, 'radius': 10, 'maxMatches': 10,
              'ambiguities': 'ignore', 'outFormat': 'json'}

    if site_object.name in cache_file:
        print('Using cache')
        return cache_file[site_object.name]
    else:
        print("Fetching")
        response = requests.get(base_url, params).json()
        cache_file[site_object.name] = response
        save_cache(cache_file)
        return cache_file[site_object.name]


def get_nearby_places(site_object):
    """Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    """
    base_url = 'http://www.mapquestapi.com/search/v2/radius'
    nearby_dict = make_request_with_cache_api(base_url, site_object)
    return nearby_dict


class NearbyPlace:
    def __init__(self, name, category, street_address, city_name):
        self.name = name
        self.category = category
        self.street_address = street_address
        self.city_name = city_name

    def info(self):
        return self.name + ' (' + self.category + '): ' + self.street_address + ', ' + self.city_name


def make_nearby_instance_list(nearby_dict):
    """
    make the nearby dictionary into instance

    Parameter:
    ------------
    nearby_dict: a dictionary contain the nearby information

    Return:
    -----------
    list of nearby place instances
    """

    nearby_instance_list = []

    for member in nearby_dict['searchResults']:
        nearby_name = member['name']

        try:
            nearby_category = member['fields']["group_sic_code_name"].strip()
            if nearby_category == '':
                nearby_category = 'no category'
        except:
            nearby_category = member['fields']["group_sic_code_name_ext"].strip()

        try:
            nearby_street_address = member['fields']['address'].strip()
            if nearby_street_address == '':
                nearby_street_address = 'no street address'
        except:
            nearby_street_address = 'no street address'

        try:
            nearby_city_name = member['fields']['city'].strip()
            if nearby_city_name == '':
                nearby_city_name = 'no city'
        except:
            nearby_city_name = 'no city'

        nearby_instance = NearbyPlace(nearby_name, nearby_category, nearby_street_address, nearby_city_name)
        nearby_instance_list.append(nearby_instance)

    return nearby_instance_list


def get_key(dictionary, value):
    """
    Input a dictionary and a value, and get the key of the value.
    ----------
    parameter:
    dictionary: dictionary
    value: a value of the dictionary, in this case it's a string
    ----------
    return

    k: string, the corresponding key for the input value.

    """

    return [k for k, v in dictionary.items() if v == value][0]


states = {'alaska': 'ak', 'alabama': 'al', 'arkansas': 'ar', 'american samoa': 'as',
          'arizona': 'az', 'california': 'ca', 'colorado': 'co', 'connecticut': 'ct',
          'district of columbia': 'dc', 'delaware': 'de', 'florida': 'fl', 'georgia': 'ga',
          'guam': 'gu', 'hawaii': 'hi', 'iowa': 'ia', 'idaho': 'id', 'illinois': 'il',
          'indiana': 'in', 'kansas': 'ks', 'kentucky': 'ky', 'louisiana': 'la',
          'massachusetts': 'ma', 'maryland': 'md', 'maine': 'me', 'michigan': 'mi',
          'minnesota': 'mn', 'missouri': 'mo', 'northern mariana islands': 'mp',
          'mississippi': 'ms', 'montana': 'mt', 'national': 'na', 'north carolina': 'nc',
          'north dakota': 'nd', 'nebraska': 'ne', 'new hampshire': 'nh', 'new jersey': 'nj',
          'new mexico': 'nm', 'nevada': 'nv', 'new york': 'ny', 'ohio': 'oh', 'oklahoma': 'ok',
          'oregon': 'or', 'pennsylvania': 'pa', 'puerto rico': 'pr', 'rhode island': 'ri',
          'south carolina': 'sc', 'south dakota': 'sd', 'tennessee': 'tn', 'texas': 'tx',
          'utah': 'ut', 'virginia': 'va', 'virgin islands': 'vi', 'vermont': 'vt',
          'washington': 'wa', 'wisconsin': 'wi', 'west virginia': 'wv', 'wyoming': 'wy'}


if __name__ == "__main__":
    base_url = 'https://www.nps.gov'
    x = 0

    while True:
        state = input('Enter a state name (e.g. Michigan, michigan) or "exit":').lower()

        if len(state) == 2 and state in states.values():
            state_url = base_url + '/' + state + '/' + '/index.htm'
        elif state == 'exit':
            break
        elif state in states.keys():
            state_url = base_url + '/' + states[state] + '/' + '/index.htm'
        else:
            print('[Error] Enter proper state name \n')
            continue
        sites_list = get_sites_for_state(state_url)

        if len(state) != 2:
            print('-' * 50)
            print("List of national sites in", state.lower())
            print('-' * 50)
        if len(state) == 2:
            print('-' * 50)
            print("List of national sites in", get_key(states, state).lower())
            print('-' * 50)

        i = 1
        while i <= len(sites_list):
            for site in sites_list:
                print('[', i, '] ', site.info())
                i += 1

        while True:
            nearby_instance_list = []
            option = input('Choose the number for detail search or "exit" or "back":').lower()
            if option == "back":
                break

            if option == "exit":
                x = 1
                break
            elif option.isnumeric():
                if int(option) <= len(sites_list) and option.isnumeric():
                    park_instance = get_site_instance(sites_list[int(option) - 1].url)
                    site_name = park_instance.name
                    nearbyplace = get_nearby_places(park_instance)  # this is the dictionary
                    nearby_instance_list = make_nearby_instance_list(nearbyplace)
                    print('-' * 50)
                    print('Places near', site_name.strip())
                    print('-' * 50)
                    for nearby_place in nearby_instance_list:
                        print("-", nearby_place.info())
                    continue
                else:
                    print("[Error] Invalid input \n")
                    print('-' * 50)
            else:
                print("[Error] Invalid input \n")
                print('-' * 50)
                continue

        if x == 1:
            break