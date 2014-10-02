"""
Client for searching Web of Science via its API.

http://wokinfo.com/media/pdf/WebServicesLiteguide.pdf
"""


#For SOAP
import suds
from suds.client import Client
import time

import logging
from logging import NullHandler
logging.getLogger(__name__).addHandler(NullHandler())
logging.getLogger('suds').setLevel(logging.ERROR)



auth_url = 'http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl'
search_url = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearchLite?wsdl'

#WOK OpenURL template.
wok_openurl = 'http://ws.isiknowledge.com/cps/openurl/service?url_ver=Z39.88-2004&rft_id=info:ut/{0}'

#Delay in seconds between queries when fetching all records
DELAY = 2


class WOS(object):

    def __init__(self):
        self.sid = None
        self.client = None
        self.auth_client = None


    def _header(self):
        return {'Cookie': 'SID=%s' % (self.sid)}


    def login(self):
        auth_client = Client(auth_url)
        self.sid = auth_client.service.authenticate()
        self.client = Client(search_url, headers=self._header())

    def logout(self):
        ac = Client(auth_url, headers=self._header())
        ac.service.closeSession()


class Search(WOS):

    def _get_all(self, first_response, retreive_params):
        """
        Walk through the results and get all of the records.
        """
        records = []
        num_found = first_response.recordsFound
        pages =  num_found / retreive_params.count
        #Add one if there is a remainder
        if num_found % retreive_params.count > 0:
            pages += 1
        logging.debug("Found {} records.  Fetching {} pages.".format(num_found, pages))
        for set_num in range(1, pages):
            logging.debug("Getting page {}".format(set_num + 1))
            retreive_params.firstRecord += retreive_params.count
            #Stop if we have reached the end.
            if retreive_params.firstRecord > num_found:
                break
            logging.debug("Pausing {} seconds between requests.".format(DELAY))
            time.sleep(DELAY)
            try:
                more = self.client.service.retrieve(first_response.queryId, retreive_params)
                records += more.records
            except suds.WebFault, e:
                #Cause: The following input is invalid [RetrieveParameter
                #firstRecord: 301  exceeds  recordsFound: 296 after deduping first 301 results].
                #Remedy: Correct your request and submit it again
                logging.debug(e)
                logging.debug('Fetch failed.  Possibly because of duplicate records error.')
                pass
        return records


    def search(self, query, sort_by_date=False, get_all=False, **kwargs):
        """
        Run a search.
        """
        logging.debug("Sending query {} to WOS.".format(query))
        #Retrieve params
        rp = self.client.factory.create('retrieveParameters')
        rp.firstRecord = kwargs.get('start', 1)
        rp.count = kwargs.get('number', 100)

        if sort_by_date is True:
            default_sort = {
                #load date
                'name': 'LD',
                #descending
                'sort': 'D'
            }
        else:
            default_sort = {}
        rp.sortField = kwargs.get('sortField', default_sort)

        #Query params.
        qp = self.client.factory.create('queryParameters')
        qp.databaseId = kwargs.get('databaseId', 'WOK')
        qp.userQuery = query
        qp.queryLanguage = 'en'

        #A list of editions to search.
        editions = kwargs.get('editions')
        if editions is not None:
            qp.editions = kwargs.get('editions', editions)

        #Time spans
        tspan = kwargs.get('timeSpan')
        if tspan is not None:
            qp.timeSpan = tspan

        sym_time_span = kwargs.get('symbolicTimeSpan')
        if sym_time_span is not None:
            qp.symbolicTimeSpan = sym_time_span

        results = self.client.service.search(qp, rp)

        num_found = results.recordsFound
        if num_found == 0:
            return []

        #Fetch all the records if get_all is True and more
        #records were found than the initial limit.
        if (get_all is True) and (num_found > rp.count):
            #Extend the initial records with all we found.
            results.records.extend(self._get_all(results, rp))
        return results

    def get(self, uid, **kwargs):
        """
        Fetch single documents.
        """
        rp = self.client.factory.create('retrieveParameters')
        rp.firstRecord = kwargs.get('start', 1)
        rp.count = 2

        rsp = self.client.service.retrieveById(
            databaseId='WOK',
            uid=uid,
            queryLanguage='en',
            retrieveParameters=rp
        )
        return rsp



class Record(object):
    """
    Single WOS result in a more useable form.
    """
    def __init__(self, record):
        """
        Init with suds record object.
        """
        self.record = record

    def title(self):
        """
        First value.
        """
        elem = self.record.title
        try:
            return elem[0].value[0]
        except:
            return None

    def authors(self):
        """
        All values for an attribute.
        """
        try:
            return self.record.authors[0].value
        except IndexError:
            return []

    def keywords(self):
        try:
            return self.record.keywords[0].value
        except:
            return []

    def _source(self):
        d = {}
        for meta in self.record.source:
            try:
                d[meta.label] = meta.value[0]
            except IndexError:
                pass
        return d

    def other(self):
        d = {}
        for meta in self.record.other:
            if meta.label == 'Identifier.Doi':
                try:
                    d['doi'] = unicode(meta.value[0])
                except IndexError:
                    pass
            elif meta.label == 'Identifier.Issn':
                try:
                    d['issn'] = unicode(meta.value[0])
                except IndexError:
                    pass
        return d

    def reseacher_ids(self):
        names = []
        rids = []
        for meta in self.record.other:
            if meta.label == 'Contributor.ResearcherID.Names':
                names += meta.value
            elif meta.label == 'Contributor.ResearcherID.ResearcherIDs':
                rids += meta.value
        out = []
        for x in range(0, len(names)):
            d = {
                'name': names[x],
                'id': rids[x]
            }
            out.append(d)
        return out

    def as_dict(self):
        """
        Output usable Python object from Suds record object.
        """
        d = {}
        d['title'] = self.title()
        d['id'] = self.record.uid
        d['authors'] = self.authors()
        sm = self._source()
        d['issue'] = sm.get('Issue')
        d['volume'] = sm.get('Volume')
        d['venue'] = sm.get('SourceTitle')
        pages = sm.get('Pages')
        d['pages'] = pages
        if pages is not None:
            try:
                start, end = pages.split('-')
                d['start'] = start
                d['end'] = end
            except ValueError:
                pass
        d['date'] = sm.get('Published.BiblioYear')
        d['url'] = wok_openurl.format(d['id'])
        d['keywords'] = self.keywords()
        d['reseacher_ids'] = self.reseacher_ids()
        #Add metadata from record.other
        d.update(self.other())
        return d

if __name__ == "__main__":
    import json
    ws = Search()
    ws.login()
    rsp = ws.search('AD=Brown Univ*', number=2)
    for rec in rsp.records:
        doc = Record(rec).as_dict()
        print json.dumps(doc, indent=2)
    #ws.logout()
