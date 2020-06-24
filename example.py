import json

from wos import Search, Record


ws = Search()
ws.login()

tspan = {'begin': '2015-05-11', 'end': '2015-05-22'}

# Limit to n results by passing in number=n.
# get_all=True to get all the records found
rsp = ws.search('AD=02912', number=10, timeSpan=tspan, get_all=True)

for rec in rsp.records:
    doc = Record(rec).as_dict()
    print(json.dumps(doc, indent=2))

ws.logout()

