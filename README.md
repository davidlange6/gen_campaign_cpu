# gen_campaign_cpu

Some simple scripts for running all requests in one or more generator campaigns as defined in MCM

Summary
  - get_requests.py gets the list of requests in a set of campaigns from MCM
  - run_campaigns.py processes a sample job from each request in a set of campaigns
  - make_table.py creates a summary table of the results from a set of campaigns

Known issues
  - Needs an AFS token, so big campaigns may need to be restarted after your shell loses its token. This is because the MCM API is AFS based. This could be avoided in a few ways..
  - the run_campaigns.py script should not be run in a cmssw environment. For reasons I don't fully understand, this interferes with the scram p command run to set up each campaign
  - the make_table.py script needs the prettytable python package. This is most easily gotten by setting up a recent CMSSW environment (which conflicts with the previous point...)
  - you need python3
  - there are a bunch of parameters hardwired in scripts that should become configurable.. They are all near the top
  
