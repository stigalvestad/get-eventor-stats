# !/usr/bin/env python


import json
import logging
import requests
import untangle
import pickle
import os.path
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import numpy as np

# urllib3.disable_warnings()

# Log configuration
logger = logging.getLogger('')
# Use below if you want to log to a file instead
# hdlr = logging.FileHandler('/x/y.log')
hdlr = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

# Replace values to match your scenario
API_KEY = ''
BASE_URL = 'https://eventor.orientering.no/api'

eventor_headers = {
    'ApiKey': API_KEY
}


def set_encoding():
    reload(sys) # just to be sure
    sys.setdefaultencoding('utf-8')

def build_eventor_api_url(relative_path):
    return BASE_URL + relative_path


def get_api_key_owner():
    response = requests.request('GET', build_eventor_api_url('/organisation/apiKey'),
                                headers=eventor_headers)
    response.raise_for_status()
    print response.text
    return response.text


def get_from_eventor(path):
    response = requests.request('GET', build_eventor_api_url(path),
                                headers=eventor_headers)
    response.raise_for_status()
    return response.text




def write_to_file(filename, content):
    with open(filename, 'wb') as f:
        pickle.dump(content, f)


def read_from_file(filename):
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        return '{}'

def post_req_example():
    utilization_body = {'agents': [], 'providers': []}
    response = requests.request('POST', build_eventor_api_url('utilization/agent/'),
                                headers=eventor_headers,
                                data=json.dumps(utilization_body))
    response.raise_for_status()
    utilization_list = response.json()
    for utilization_item in utilization_list:
        print '' + utilization_item['agent'] + '-' + utilization_item['provider'] + ': ' + `utilization_item[
            'currentLoad']` + '/' + `utilization_item['maxLimit']`
    return


# race-class-club
def get_race_club_class_list(starts_dict, year, type):
    race_name = starts_dict.StartList.Event.Name.cdata
    race_id = starts_dict.StartList.Event.EventId.cdata
    # print race_name

    race_class_club = []
    # print starts_dict.StartList.ClassStart
    for class_start in starts_dict.StartList.ClassStart:
        class_name = class_start.EventClass.Name.cdata
        # print 'Processing ' + class_name
        for person_start in class_start.PersonStart:
            org = person_start.Organisation.Name.cdata
            org_name = org
            try:
                org = person_start.Organisation.OrganisationId.cdata
            except:
                # except AttributeError:
                print 'Revert to using org name instead of org id: ' + org

            rcc = {
                'year': year,
                'type': type,
                'race': race_id,
                'class': class_name,
                'club': org,
                'clubName': org_name
            }
            # print rcc
            race_class_club.append(rcc)
    return race_class_club


set_encoding()
# print 'do something'
# owner_text = get_api_key_owner()
# owner_doc = untangle.parse(owner_text)
# print owner_doc.Organisation.Name.cdata


# 4893: 2015 sm lang
# 4790: 2015 sm mellom sogne
# 6686: 2016 sm lang
# 6687: 2016 sm mellom vegardshei
# 8356: 2017 sm lang
# 8357: 2017 sm mellom vennesla
# 9206: 2018 sm lang
# 9210: 2018 sm mellom arendal

long_distances = [{'year': 2018, 'id': '9206', 'type': 'long'}, {'year': 2017, 'id': '8356', 'type': 'long'}, {'year': 2016, 'id': '6686', 'type': 'long'}, {'year': 2015, 'id': '4893', 'type': 'long'}]
middle_distances = [{'year': 2018, 'id': '9210', 'type': 'middle'}, {'year': 2017, 'id': '8357', 'type': 'middle'}, {'year': 2016, 'id': '6687', 'type': 'middle'}, {'year': 2015, 'id': '4790', 'type': 'middle'}]


def make_rcc_list(races_list):
    rcc_list = []
    for race in races_list:
        starts = untangle.parse(get_from_eventor('/starts/event?eventId=' + race['id']))
        rcc_list_new = get_race_club_class_list(starts, race['year'], race['type'])
        for rcc in rcc_list_new:
            rcc_list.append(rcc)
    return rcc_list


def make_club_plot(runners_per_year_club, description):
    title = 'Antall deltakere per klubb ' + description
    grid = sns.FacetGrid(runners_per_year_club, col="clubName", hue="year", col_wrap=4, height=2)
    grid.map(plt.plot, "year", "class", marker="o")

    # Adjust the tick positions and labels
    grid.set(xticks=[2016, 2018], xlim=(2014, 2019))
    # grid.set(xticks=[2016, 2018], yticks=[5, 10, 30], xlim=(2014, 2019))
    axes = grid.axes.flatten()
    for axis in axes:
        axis.set_ylabel('')
        axis.set_title(axis.get_title().replace('clubName = ', ''))
    plt.suptitle(title, fontsize=16)
    plt.savefig(title.replace(" ", "_"))


def make_class_plot(runners_per_year_class, description):
    title = 'Antall deltakere per klasse ' + description
    grid = sns.FacetGrid(runners_per_year_class, col="class", hue="year", col_wrap=4, height=2)
    grid.map(plt.plot, "year", "clubName", marker="o")

    # Adjust the tick positions and labels
    # grid.set(xticks=[2016, 2018], yticks=[5, 10, 30], xlim=(2014, 2019))
    axes = grid.axes.flatten()
    for axis in axes:
        axis.set_ylabel('')
        axis.set_title(axis.get_title().replace('class = ', ''))
    plt.suptitle(title, fontsize=16)
    plt.savefig(title.replace(" ", "_"))


def analyse_rcc_list(rccs, description):
    data = pd.DataFrame(rccs)

    print 'Hvor mange deltakere var med i hver klasse hvert aar?'
    runners_per_year_class = data.groupby(['year', 'class'], as_index=False)['clubName'].count()
    print runners_per_year_class
    make_class_plot(runners_per_year_class, description)

    print 'Hvor mange deltakere var med fra hver klubb hvert aar?'
    runners_per_year_club = data.groupby(['year', 'clubName'], as_index=False)['class'].count()
    print runners_per_year_club
    print list(runners_per_year_club.columns.values)

    make_club_plot(runners_per_year_club, description)
    # plt.show()


def test_seaborn():
    df = pd.DataFrame()

    df['x'] = random.sample(range(1, 100), 25)
    df['y'] = random.sample(range(1, 100), 25)

    print df.head()

    # sns.lmplot('x', 'y', data=df, fit_reg=False)
    sns.relplot('x', 'y', data=df)
    plt.show()
    # sns.kdeplot(df.y)
    #
    # sns.kdeplot(df.y, df.x)


# test_seaborn()

# rcc_long = make_rcc_list(long_distances)
# rcc_middle = make_rcc_list(middle_distances)

# write_to_file('rcc_long.data', rcc_long)
# write_to_file('rcc_middle.data', rcc_middle)

rcc_long = read_from_file('rcc_long.data')
rcc_middle = read_from_file('rcc_middle.data')
print rcc_long[0]
analyse_rcc_list(rcc_long, 'Langdistanse')
analyse_rcc_list(rcc_middle, 'Mellomdistanse')
analyse_rcc_list(rcc_long + rcc_middle, 'Lang og Mellom')

# analyse_rcc_list(rcc_middle)
# rcc_middle = make_rcc_list(middle_distances)

# plt.plot(range(10))
# plt.show()