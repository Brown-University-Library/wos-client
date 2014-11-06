
from collections import defaultdict, namedtuple
import os
import pickle
import string

from vdm.backend import FusekiGraph
from vdm.utils import get_env

from nameparser import HumanName

punctuation = set(string.punctuation)
def clean_string(raw):
    raw = raw.strip().lower()
    s = ''.join(ch for ch in raw if ch not in punctuation)
    return s

#This has to be declared outside of the function for pickling.
#http://stackoverflow.com/questions/16377215/how-to-pickle-a-namedtuple-instance-correctly
Fac = namedtuple('Fac', ['uri', 'full', 'last', 'given', 'first_initial', 'middle', 'middle_initial'])
def get_names():
    endpoint = FusekiGraph(get_env('VIVO_ENDPOINT'))
    pickle_file = os.path.join(os.getcwd(), '/tmp/vdm_names.pkl')
    if not os.path.exists(pickle_file):
        output = open(pickle_file, 'wb')
        names_q = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX vivo: <http://vivoweb.org/ontology/core#>
        SELECT DISTINCT ?fac ?last ?first ?middle
        WHERE
        {
              ?fac a vivo:FacultyMember .
              ?fac foaf:lastName ?last;
                   foaf:firstName ?first.
              OPTIONAL {?fac vivo:middleName ?middle.}
        } ORDER BY ?last
        """
        results = endpoint.query(names_q)
        #Read the names of faculty into a default dict like this
        #'smith': ['Smith, Tom', 'Smith, Sally']
        names = defaultdict(list)
        for row in results:
            last = row.last.toPython().lower()
            first = row.first.toPython().lower()
            if row.middle is not None:
                middle = row.middle.toPython().lower()
                full = u"{}, {} {}.".format(last, first, middle[0])
                mi = middle[0]
            else:
                middle = None
                mi = None
                full = u"{}, {}".format(last, first)
            uri = row.fac
            name_key = clean_string(last)
            f = Fac(full=full, last=last, given=first, uri=uri, first_initial=first[0], middle=middle, middle_initial=mi)
            names[name_key].append(f)
        pickle.dump(names, output)
        output.close()
        return names
    else:
        pfile = open(pickle_file, 'rb')
        names = pickle.load(pfile)
        pfile.close()
        return names


Author = namedtuple('Fac', ['full', 'last', 'given', 'first_initial', 'middle', 'middle_initial'])
def chunk_name(name_str):
    """
    Split WOK style names into last, first initial, middle initial.
    """
    name = HumanName(name_str)
    last = name.last.lower()
    given = name.first.lower()
    middle = name.middle.lower()
    mi = None
    if middle is not None:
        try:
            mi = middle[0]
        except IndexError:
            pass
    fi = given[0]
    au = Author(full=name_str.lower(), last=last, given=given, first_initial=fi, middle=middle, middle_initial=mi)
    return au

if __name__ == "__main__":
    names = get_names()
