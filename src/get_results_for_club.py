# !/usr/bin/env python


import logging
import requests
import untangle
import sys
import pandas as pd

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
ORG_ID_CLUB = 135
PERIOD_START = '2019-01-01'
PERIOD_END = '2019-12-31'

eventor_headers = {
    'ApiKey': API_KEY
}


def set_encoding():
    reload(sys) # just to be sure
    sys.setdefaultencoding('utf-8')


def build_eventor_api_url(relative_path):
    url = BASE_URL + relative_path
    print url
    return url


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
    print response.text
    return response.text


def get_results_for_person(person):
    results_list = []
    results_for_person = untangle.parse(get_from_eventor('/results/person?fromDate=' + PERIOD_START + '&toDate=' + PERIOD_END + '&personId=' + person['id']))
    print('got results')
    for result_list in results_for_person.ResultListList:
        print result_list
        if len(result_list.children) > 0:
            for result in result_list.ResultList:
                event_name = result.Event.Name.cdata
                event_date = result.Event.StartDate.Date.cdata
                event_id = result.Event.EventId.cdata
                try:
                    event_race_position = result.ClassResult.PersonResult.Result.ResultPosition.cdata
                except AttributeError:
                    print('result position was missing, replacing with empty')
                    event_race_position = ''

                try:
                    event_race_time = result.ClassResult.PersonResult.Result.Time.cdata
                except AttributeError:
                    print('event_race_time was missing, replacing with empty')
                    event_race_time = ''

                try:
                    event_race_time_diff = result.ClassResult.PersonResult.Result.TimeDiff.cdata
                except AttributeError:
                    print('time diff was missing, replacing with empty')
                    event_race_time_diff = ''

                try:
                    event_race_status = result.ClassResult.PersonResult.Result.CompetitorStatus['value']
                except AttributeError:
                    print('event_race_status was missing, replacing with empty')
                    event_race_status = ''

                event_class_name = result.ClassResult.EventClass.Name.cdata
                event_class_name_short = result.ClassResult.EventClass.ClassShortName.cdata
                event_class_nof_entries = result.ClassResult.EventClass.ClassRaceInfo['noOfStarts']
                result = {
                    'event_name': event_name,
                    'event_id': event_id,
                    'event_date': event_date,
                    'event_race_position': event_race_position,
                    'event_race_time': event_race_time,
                    'event_race_time_diff': event_race_time_diff,
                    'event_race_status': event_race_status,
                    'event_class_name': event_class_name,
                    'event_class_name_short': event_class_name_short,
                    'event_class_nof_entries': event_class_nof_entries
                }
                person_with_result = person.copy()
                person_with_result.update(result)
                results_list.append(person_with_result)
                # print result
    print('Found ' + `len(results_list)` + ' results for ' + person['name'])
    return results_list


def get_persons_in_club(org_id):
    persons_in_club = untangle.parse(get_from_eventor('/persons/organisations/' + `org_id`))
    # persons_in_club.raise_for_status()
    persons = []
    for person in persons_in_club.PersonList:
        # print person
        for p2 in person.Person:
            name = p2.PersonName.Given.cdata + ' ' + p2.PersonName.Family.cdata
            person_id = p2.PersonId.cdata
            birth_year = p2.BirthDate.Date.cdata.split('-')[0]
            person_sex = p2['sex'] # M = male, F = female
            print(name + ' (' + `person_id` + ')[' + person_sex + ']')
            persons.append({
                'name': name,
                'id': person_id,
                'sex': person_sex,
                'birth_year': birth_year
            })
    return persons


def get_results_for_all_persons(persons_in_club):
    all_results = []
    for person_in_club in persons_in_club:
        results_for_person = get_results_for_person(person_in_club)
        all_results = all_results + results_for_person
    return all_results


def export_to_csv(all_results):
    df = pd.DataFrame(all_results)
    # reorder and filter which columns to export to csv
    df = df[['id', 'name', 'birth_year', 'event_name', 'event_date', 'event_class_name', 'event_race_status',
             'event_race_position', 'event_class_nof_entries', 'event_race_time', 'event_race_time_diff']]

    df.to_csv('all_results_grane_members_2019.csv', sep='\t', encoding='utf-8')


set_encoding()

persons_in_club = get_persons_in_club(ORG_ID_CLUB)
all_results_for_all_persons = get_results_for_all_persons(persons_in_club)
export_to_csv(all_results_for_all_persons)

