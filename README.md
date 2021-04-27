# gen_campaign_cpu

Some simple scripts for running all requests in one or more generator campaigns as defined in MCM

Known issues
  - Needs an AFS token, so big campaigns may need to be restarted after your shell loses its token. This is because the MCM API is AFS based. This could be avoided in a few ways..
  - the run_campaigns.py script should not be run in a cmssw environment. For reasons I don't fully understand, this interferes with the scram p command run to set up each campaign
  - the make_table.py script needs the prettytable python package. This is most easily gotten by setting up a recent CMSSW environment (which conflicts with the previous point...)
  - you need python3
