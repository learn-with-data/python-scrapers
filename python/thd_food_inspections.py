'''Scrape www.tulsa-health.org/food-safety/restaurant-inspections'''
import re
import sys
import time
from itertools import izip_longest

RUNNING_IN_SCRAPERWIKI = False
try:
    import scraperwiki
    RUNNING_IN_SCRAPERWIKI = True
except ImportError:
    pass

import requests
from pyquery import PyQuery as pq

THD_ROOT = 'http://tulsa.ok.gegov.com/tulsa'

SEARCH_DATA = {'startrow': 1,
               'source': 'quick',
               'precision': 'LIKE',
               'startDate': '01-07-2011',
               'endDate': '01-07-2012',
               'establishmentClass': 'ANY',
               'maxrows': 10,
               'filter': 'est',
               'Search': 'Search'}


# http://stackoverflow.com/q/434287/571420
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    search_resp = requests.post(THD_ROOT + '/index.cfm', data=SEARCH_DATA)
    facility_links = pq(search_resp.content).find(
        'div#searchResults a.resultMore')
    for f_link in facility_links:
        facility_href = pq(f_link).attr('href')
        facility_resp = requests.get(THD_ROOT + '/' + facility_href)
        inspection_links = pq(facility_resp.content).find(
            'div#inspectionHistory a')
        for i_link in inspection_links:
            inspection_href = pq(i_link).attr('href')
            inspection_resp = requests.get(THD_ROOT + '/' + inspection_href)
            doc = pq(inspection_resp.content)
            inspection = {}

            inspection['name'] = doc.find(
                'div#inspectionDetail h3').text()
            m = re.search('Location: (?P<location>.*)<br/>',
                         doc.find('div#inspectionDetail').html())
            inspection['location'] = m.group('location').strip()
            info = doc.find('div#inspectionInfo tr td')
            for (counter, pair) in enumerate(grouper(info, 2)):
                value = pq(pair[1]).text()
                if counter == 0:
                    inspection['date'] = value
                elif counter == 4:
                    inspection['result'] = value

            print inspection

            if RUNNING_IN_SCRAPERWIKI:
                scraperwiki.sqlite.save(unique_keys=['name', 'date'],
                                        data=inspection)

            time.sleep(1)

if RUNNING_IN_SCRAPERWIKI:
    main()
else:
    if __name__ == "__main__":
        sys.exit(main())
