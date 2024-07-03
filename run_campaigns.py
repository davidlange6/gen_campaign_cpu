#!/usr/bin/env python3

import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps
from subprocess import Popen,PIPE
import os

campaigns=sys.argv[1:]
if len(campaigns)==0:
    campaigns= ["RunIISummer20UL18wmLHEGEN","RunIISummer20UL18pLHEGEN","RunIISummer20UL18GEN"]

#nThread=8
nThread=16#32
#optionally re-use the mcm information in job subdirectories
use_existing_job_info=False
#if false, it just does the mcm query
run_job=True
#maximum number of workflows to try to run (a big number just means to run all)
nmax=400000
#skip workflows in "new" status in mcm
skip_new=False

#lacking useful information from mcm, we may have to guess at how many events to 
#run and how long they take
default_time_evt = 10
default_events = 40

target_job_length=1200
minimum_number_of_events = 100
minimum_events_after_filter = 15.


def runCommand(comm):
    p = Popen(comm,stdout=PIPE,stderr=PIPE,shell=True)
    pipe=p.stdout.read()
    errpipe=p.stderr.read()
    tupleP=os.waitpid(p.pid,0)
    eC=tupleP[1]
    return eC,pipe.decode(encoding='UTF-8'),errpipe.decode(encoding='UTF-8')

if not use_existing_job_info:
    #mcm = McM(dev=True)
    mcm = McM(id='oidc', dev=True) #, debug=True)
    
def do_request(request):

    print("Starting "+request)

    #just run the job if use_existing_job_info is set
    if (use_existing_job_info) and os.path.exists(os.path.join(request,'run.sh')):
        ec,c_out,c_err=runCommand("cd "+request+"; ./run.sh")
        if ec!=0:
            print(c_out)
            print(c_err)
            return

        print("Done "+request)
        return

    #otherwise, query mcm for the request
    single_request = mcm.get('requests', request, method='get')
    total_events=single_request["total_events"]
    release=single_request["cmssw_release"]
    if len(single_request["generator_parameters"])> 0:
        matching=single_request["generator_parameters"][-1]["match_efficiency"]
        filter_eff=single_request["generator_parameters"][-1]["filter_efficiency"]
    else:
        matching=1.
        filter_eff=1.
    if "validation" in single_request and "results" in single_request["validation"]:
        validation=single_request["validation"]["results"]
        if "1" in validation:
            results=validation["1"]
        else:
            if "8" in validation:
                results=validation["8"]
            else:
                print("Seems there is no useful validation information- guessing - "+request)
                results=None
        
        if results:
            time_event = int(results["time_per_event"])
            events = int(results["total_events"])
        else:
            time_event = default_time_evt
            events = default_events
    else:
        time_event = default_time_evt
        events=default_events

    #set up directory for request and fill it
    ec,c_out,c_err=runCommand("mkdir -p "+request)
    if ec!=0:
        print(c_out)
        print(c_err)
        return

    #store a summary of information
    finfo=open(os.path.join(request,"info.txt"),"w")
    finfo.write("Events: "+str(total_events)+'\n')
    finfo.write("cmssw_release: "+release+'\n')
    finfo.write("Matching: "+str(matching)+'\n')
    finfo.write("Filter: "+str(filter_eff)+'\n')
    finfo.write("Time/evt: "+str(time_event)+'\n')
    finfo.write("Val events: "+str(events)+'\n')
    finfo.close()
    
    fragment=single_request["fragment"]
    #aack - externalLHEProducer sets its own number of events...
    if 'externalLHEProducer' in fragment:
        loc=fragment.find("nEvents = cms.untracked.uint32(5000)")
        nchar=len("nEvents = cms.untracked.uint32(5000)")
        fragment = 'import os\n'+fragment[:loc]+"nEvents = cms.untracked.uint32(int(os.environ['NEVT']))"+fragment[loc+nchar:]
    #save the fragment        
    frag=open(os.path.join(request,'frag.py'),'w')
    frag.write(fragment)
    frag.write('\n')
    frag.close()
    
    cmsdrivers = mcm.get('requests', request, method='get_cmsDrivers')
    if not cmsdrivers:
        print("no cmsdriver")
        return
    events_to_run=0 
    if float(time_event) > 0.0: events_to_run=int(target_job_length/float(time_event))
    if events_to_run < minimum_number_of_events: events_to_run = minimum_number_of_events
    #watch out for low efficiency stuff
    if events_to_run * filter_eff < minimum_events_after_filter:
        events_to_run = int(minimum_events_after_filter/filter_eff)


    fscript=open(os.path.join(request,"run.sh"),'w')
    fscript.write("#!/bin/sh\n")
    fscript.write("scram p "+release+"; cd "+release+"\n")
    fscript.write("eval `scramv1 runtime -sh`\n")
    fscript.write("mkdir -p src/Configuration/Gen/python\n")
    fscript.write("export NEVT="+str(events_to_run)+"\n")
    fscript.write("cp ../frag.py src/Configuration/Gen/python\n")
    fscript.write("scram b\n")
    for i,cmsdriver in enumerate(cmsdrivers):
        sp=cmsdriver.split()
        sp[1]="Configuration/Gen/frag"
        driver=" ".join(sp)
        driver=driver+" -n $NEVT "#+str(events_to_run)
        #force one thread
        driver=driver+' --nThreads 1 --suffix "-j JobReport1.xml "'
        driver=driver+' --customise Validation/Performance/TimeMemorySummary.customiseWithTimeMemorySummary'
        #driver=driver+" --prefix '/dlange/gen/monitor_workflow.py timeout --signal SIGTERM 17200 '"
        driver=driver+' > run.log 2>&1'
        fscript.write(driver+"\n")
        fscript.write('if [ $? -ne 0 ]\nthen\necho "cmsenv failed"\nexit 1\nfi\n')
        fscript.write("mv JobReport1.xml ../"+request+"_"+str(i)+".xml\n")
        fscript.write("gzip run.log; mv run.log.gz ../run_"+str(i)+".log.gz \n")
    fscript.write("cd ..\n")
    fscript.write("rm -rf "+release+"\n")
    fscript.close()
    runCommand("chmod +x "+os.path.join(request,"run.sh"))

    if run_job:
        ec,c_out,c_err=runCommand("cd "+request+"; ./run.sh")
        if ec!=0:
            print(c_out)
            print(c_err)
            return

    print("Done "+request)
    return


from threading import Thread
import queue
import time

#simple thread queue manager
class Worker(Thread):
    def __init__(self, q, other_arg, *args, **kwargs):
        self.q = q
        self.other_arg = other_arg
        super().__init__(*args, **kwargs)
    def run(self):
        while True:
            try:
                work = self.q.get(timeout=3)  # 3s timeout
                do_request(work)
                #don't blow up mcm so often..
                time.sleep(1)
            except queue.Empty:
                return
            # do whatever work you have to do on work
            self.q.task_done()

do_work = queue.Queue()

new_requests={}
for campaign in campaigns:
    f=open(campaign+"_new.txt") #this used to be _new.txt for /gen area
    for l in f:
        if "Single request" in l: break
        request=l.strip()
        new_requests[request]=1
    f.close()


i=0
requests={}
for campaign in campaigns:
    f=open(campaign+".txt")
    for l in f:
        if "Single request" in l: break
        request=l.strip()
        print(request)
        if request in requests:
            print("odd duplicate "+request)
            continue
        if os.path.exists(os.path.join(request,request+"_0.xml")):
            print("Already done")
            continue
        if os.path.exists(os.path.join(request,request+".xml")):
            print("Already done")
            continue
        if skip_new and request in new_requests: 
            print("Skipping new")
            continue
        requests[request]=i
        i=i+1
        do_work.put(request)
        if i==nmax: break
    if i==nmax: break


otherarg=''
for _ in range(nThread):
    Worker(do_work, otherarg).start()

do_work.join()
