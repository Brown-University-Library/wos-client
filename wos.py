"""
Client for searching Web of Science via its API.

http://wokinfo.com/media/pdf/WebServicesLiteguide.pdf
"""


#For SOAP
import suds
from suds.client import Client

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

logging.getLogger('suds.client').setLevel(logging.ERROR)

auth_url = 'http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl'
search_url = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearchLite?wsdl'

#WOK OpenURL template.
wok_openurl = 'http://ws.isiknowledge.com/cps/openurl/service?url_ver=Z39.88-2004&rft_id=info:ut/{0}'

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

    def search(self, query, **kwargs):
        """
        Run a search.
        """
        #Retrieve params
        rp = self.client.factory.create('retrieveParameters')
        rp.firstRecord = kwargs.get('start', 1)
        rp.count = kwargs.get('number', 100)
        default_sort = {
            #load date
            'name': 'LD',
            #descending
            'sort': 'D'
        }
        rp.sortField = kwargs.get('sortField', default_sort)

        #Query params.
        qp = self.client.factory.create('queryParameters')
        qp.databaseId = 'WOS'
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
        return results

    def get(self, uid, **kwargs):
        """
        Fetch single documents.
        """
        rp = self.client.factory.create('retrieveParameters')
        rp.firstRecord = kwargs.get('start', 1)
        rp.count = 2

        rsp = self.client.service.retrieveById(
            databaseId='WOS',
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
        if pages is not None:
            start, end = pages.split('-')
            d['start'] = start
            d['end'] = end
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
