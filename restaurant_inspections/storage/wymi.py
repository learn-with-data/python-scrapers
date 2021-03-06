import json
import os
import string
import urlparse
from urllib import urlencode

import requests

STORING_TO_WYMI = False
if 'WYMI_API_KEY' in os.environ:
    WYMI_API_KEY = os.environ['WYMI_API_KEY']
    WYMI_API_HOST = os.environ['WYMI_API_HOST']
    WYMI_API_ROOT = os.environ['WYMI_API_ROOT']
    WYMI_USERNAME = os.environ['WYMI_USERNAME']
    if WYMI_API_KEY and WYMI_API_HOST and WYMI_API_ROOT and WYMI_USERNAME:
        WYMI_API = "http://" + WYMI_API_HOST + WYMI_API_ROOT
        STORING_TO_WYMI = True
        print "Storing to wymi"
    else:
        print ("You must set WYMI_USERNAME, WYMI_API_KEY, WYMI_API_HOST, and "
              "WYMI_API_ROOT environment variables to store to WYMI.")


def save_facility(facility):
    if STORING_TO_WYMI:
        # check for existing record
        check_params = {
            'username': WYMI_USERNAME,
            'api_key': WYMI_API_KEY,
            'name': facility['name'],
            'address': facility['location'],
        }
        check_url = "%s/facility/?%s" % (WYMI_API, urlencode(check_params))
        results_resp = requests.get(check_url)
        if results_resp.status_code == 200:
            results = json.loads(results_resp.content)
            if results['meta']['total_count'] > 0:
                facility['id'] = results['objects'][0]['id']
        req_data = {
            'name': facility['name'],
            'address': facility['location'],
            'city': 'Tulsa',
            'state': 'OK',
            'type': facility['type'],
            'zip_code': '',
            'latitude': "%.8g" % facility['latitude'],
            'longitude': "%.8g" % facility['longitude'],
        }
        facility_token = ''
        # TODO refactor into build_wymi_url
        if 'id' in facility:
            facility_token = '%s/' % facility['id']
        wymi_url = "%s/facility/%s?username=%s&api_key=%s" % (
            WYMI_API, facility_token, WYMI_USERNAME, WYMI_API_KEY)
        req_content = json.dumps(req_data)
        req_headers = {"content-type": "application/json"}
        if 'id' in facility:
            requests.put(wymi_url, req_content, headers=req_headers)
            return facility['id']
        else:
            resp = requests.post(wymi_url, req_content, headers=req_headers)
            facility_id = parse_id_from_location(resp.headers['location'])
            return facility_id


def save_inspection(inspection):
    if STORING_TO_WYMI:
        inspection_date = inspection['date'].strftime('%Y-%m-%d')
        check_params = {
            'username': WYMI_USERNAME,
            'api_key': WYMI_API_KEY,
            'facility': inspection['facility_id'],
            'date': inspection_date,
        }
        check_url = "%s/inspection/?%s" % (WYMI_API, urlencode(check_params))
        results_resp = requests.get(check_url)
        if results_resp.status_code == 200:
            results = json.loads(results_resp.content)
            if results['meta']['total_count'] > 0:
                inspection['id'] = results['objects'][0]['id']
        facility_resource_id = "%s/facility/%s/" % (WYMI_API_ROOT,
                                                    inspection['facility_id'])
        score = -1
        if 'score' in inspection:
            score = inspection['score']
        req_data = {
            'facility': facility_resource_id,
            'date': inspection_date,
            'score': score,
            'type': inspection['purpose']
        }
        # TODO refactor into build_wymi_url
        inspection_token = ''
        if 'id' in inspection:
            inspection_token = '%s/' % inspection['id']
        wymi_url = "%s/inspection/%s?username=%s&api_key=%s" % ( WYMI_API,
            inspection_token, WYMI_USERNAME, WYMI_API_KEY)
        req_content = json.dumps(req_data)
        req_headers = {"content-type": "application/json"}
        if 'id' in inspection:
            requests.put(wymi_url, req_content, headers=req_headers)
            return inspection['id']
        else:
            resp = requests.post(wymi_url, req_content, headers=req_headers)
            inspection_id = parse_id_from_location(resp.headers['location'])
            return inspection_id


def save_violation(violation):
    if STORING_TO_WYMI:
        check_params = {
            'username': WYMI_USERNAME,
            'api_key': WYMI_API_KEY,
            'inspection': violation['inspection']['id'],
            'code': violation['food_code'],
        }
        check_url = "%s/violation/?%s" % (WYMI_API, urlencode(check_params))
        results_resp = requests.get(check_url)
        if results_resp.status_code == 200:
            results = json.loads(results_resp.content)
            if results['meta']['total_count'] > 0:
                violation['id'] = results['objects'][0]['id']
        req_data = {
            'inspection': "%s/inspection/%s/" % (WYMI_API_ROOT,
                                             violation['inspection']['id']),
            'type': violation['type'],
            'details': violation['comments'],
            'code': violation['food_code'],
        }
        # TODO refactor into build_wymi_url
        violation_token = ''
        if 'id' in violation:
            violation_token = '%s/' % violation['id']
        wymi_url = "http://%s%s/violation/%s?username=%s&api_key=%s" % (
            WYMI_API_HOST, WYMI_API_ROOT, violation_token, WYMI_USERNAME,
            WYMI_API_KEY)
        req_content = json.dumps(req_data)
        req_headers = {"content-type": "application/json"}
        try:
            if 'id' in violation:
                requests.put(wymi_url, req_content, headers=req_headers)
                return violation['id']
            else:
                resp = requests.post(wymi_url, req_content, headers=req_headers)
                violation_id = parse_id_from_location(resp.headers['location'])
                return violation_id
        except:
            pass


def parse_id_from_location(location):
    parts = urlparse.urlparse(location)
    id = string.split(string.strip(parts.path, '/'), '/')[-1]
    return id
