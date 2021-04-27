import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=True)

# Example to get  ALL requests which are member of a given campaign and are submitted
# It uses a generic search for specified columns: query='status=submitted'
# Queries can be combined: query='status=submitted&member_of_campaign=Summer12'

campaigns= ["RunIISummer20UL18wmLHEGEN","RunIISummer20UL18pLHEGEN","RunIISummer20UL18GEN"]

for campaign in campaigns:
    f=open(campaign+"_new.txt",'w')
    campaign_requests = mcm.get('requests', query='member_of_campaign='+campaign+'&status=new')
    for request in campaign_requests:
        f.write(request['prepid']+"\n")
    f.close()
   
    f=open(campaign+".txt",'w')
    campaign_requests = mcm.get('requests', query='member_of_campaign='+campaign)     
    for request in campaign_requests:
        f.write(request['prepid']+"\n")

    cmsdrivers = mcm.get('campaigns', campaign, method='get_cmsDrivers')
    f.write('Single request "%s":\n%s' % (campaign, dumps(cmsdrivers, indent=4)))
    f.write('\n')
    f.close()
