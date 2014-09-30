#wos-client

Client code for the Web of Science API.

 * The WOS API is documentated at: http://wokinfo.com/media/pdf/WebServicesLiteguide.pdf.

 * This code needs to run from a machine within an IP address range that subscribes to WOS.


##usage
`
import json
ws = Search()
ws.login()
rsp = ws.search('AD=Brown Univ*', number=2)
for rec in rsp.records:
    doc = Result(rec).as_dict()
    print json.dumps(doc, indent=2)
ws.logout()
`

