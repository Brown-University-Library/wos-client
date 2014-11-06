
from wos import Search, Record

from utils import chunk_name, get_names

from vdm.namespaces import D

import json

import logging

logger = logging.getLogger()
formatter = logging.Formatter(u'%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

ahci = [{'collection': 'WOS', 'edition': 'AHCI'}]

# harvested = []

# ws = Search()
# ws.login()
# tspan = {'begin': '2014-01-01', 'end': '2014-12-31'}
# rsp = ws.search('AD=02912', editions=ahci, timeSpan=tspan, get_all=True)
# for rec in rsp.records:
#     doc = Record(rec).as_dict()
#     #print json.dumps(doc, indent=2)
#     harvested.append(doc)

# with open('data/ahci_2014_all.json', 'wb') as outf:
#    json.dump(harvested, outf)

# #print json.dumps(harvested, indent=2)

# ws.logout()


# with open('/tmp/phealth-harvested.json') as pfile:
#     phealth_harvested = [D[f] for f in json.load(pfile)]

cr = 'http://crossref.org/openurl/?issn={}&date={}&volume={}&spage={}&noredirect=true&pid=tlawless@brown.edu&format=unixref'

names = get_names()

with open('data/ahci_2014_all.json') as hf:
    harvested = json.load(hf)

for pub in harvested:
    authors = pub.get('authors', [])
    if len(authors) >= 10:
        continue
    for au in authors:
        nc = chunk_name(au)
        match = names.get(nc.last)
        if match is not None:
            for mau in match:
                if nc.full == mau.full:
                    doi = pub.get('doi')
                    #if doi is not None:
                    #    continue
                    #if mau.uri not in phealth_harvested:
                    #    continue
                    # print pub['id'], doi
                    # print pub['url']
                    # print mau.full, mau.uri

                    # if doi is None:
                    #     print cr.format(
                    #         pub.get('issn'),
                    #         pub.get('date'),
                    #         pub.get('volume'),
                    #         pub.get('start')
                    #     )
                    # print
                else:
                    #For now pass, but look at first initial in later pass.
                    if (nc.last == mau.last) and (nc.first_initial == mau.first_initial):
                        doi = pub.get('doi')
                        print pub['id'], doi
                        print pub['url']
                        print mau.full, mau.uri

                        if doi is None:
                            print cr.format(
                                pub.get('issn'),
                                pub.get('date'),
                                pub.get('volume'),
                                pub.get('start')
                            )
                        print
                        pass
