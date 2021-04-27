#!/usr/bin/env python

campaigns= ["RunIISummer20UL18wmLHEGEN","RunIISummer20UL18pLHEGEN","RunIISummer20UL18GEN"]
import os

requests={}
new_requests={}
for campaign in campaigns:
    f=open(campaign+"_new.txt")
    for l in f:
        if "Single request" in l: break
        request=l.strip()
        new_requests[request]=1
    f.close()
    f=open(campaign+".txt")
    for l in f:
        if "Single request" in l: break
        request=l.strip()

        xmls=[request+'.xml',request+"_0.xml",request+"_1.xml"]
        requests[request]={}
        r=requests[request]
        foundxml=False
        for xml in xmls:
            xmlf=os.path.join(request,xml)
            if not os.path.exists(xmlf):
                continue
            foundxml=True
            for l2 in open(xmlf):
                atts=["TotalLoopCPU","TotalJobTime","TotalLoopTime","TotalInitTime"]
                for att in atts:
                    if att in l2:
                        #add them
                        r[att]=r.get(att,0.)+float(l2.split('=')[2].split('"')[1])
                if "<TotalEvents>" in l2:
                    #last xml wins
                    r["OutputEvents"]=int(l2.split(">")[1].split("<")[0])

        if not foundxml:
            requests[request]={}
            continue

        for l2 in open(os.path.join(request,"run.sh")):
            if " -n " in l2:
                loc=l2.rfind(' -n ')
                nevt=l2[loc+1:].split()[1]
                if "NEVT" not in nevt:
                    r["RunEvents"] = int(nevt)
            if "NEVT=" in l2:
                r["RunEvents"]=int(l2.split('=')[1])

        for l2 in open(os.path.join(request,"info.txt")):
            if l2.startswith("Events: "):
                r["NeededEvents"]=int(l2.split()[1])

        gen_type="Unknown"
        known_gens=["powheg","madgraph","mcfm","EvtGen","jhugen","Tauola","Pythia8"]
        with open(os.path.join(request,"frag.py")) as file:
            fragfile = file.read()
            for gen in known_gens:
                if gen in fragfile:
                    gen_type=gen
                    break
        r["GenType"]=gen_type

print(len(requests))

nEmpty=0
nFull=0
empties=[]
from prettytable import PrettyTable
myTable=PrettyTable(["Request","kevents","CPU/Evt","In/Out","CPU/SimEvt","Eff","InitTime","CPUNeed-ksec","Generator"])
myTable.float_format = "6.2"
myTable.int_format = "8"
myTable.sortby="CPUNeed-ksec"
myTable.reversesort=True
totals=[0,0,0]
gen_total={}
gen_total_ev={}
for request in requests:
    r=requests[request]
    if len(r)==0:
        nEmpty+=1
        empties.append(request)
        continue
    nFull+=1
    need_evts = r["NeededEvents"] // 1000
    cpu_evt = r["TotalLoopCPU"]/r["RunEvents"]
    eff = r["TotalLoopCPU"]/r["TotalLoopTime"]
    init_time = r["TotalInitTime"]
    output_eff=r["OutputEvents"]/r["RunEvents"]
    if r["OutputEvents"]==0.:
        print("odd",request,r["RunEvents"],r["OutputEvents"])
        output_eff=1.
    cpu_need = r["NeededEvents"]*cpu_evt/output_eff #the needed events in mcm is the number of events to run in detector simulation
    if r["GenType"] == "EvtGen":
        cpu_need *= 0.5 # hack - we know current pythia software is faster than the UL version
    myTable.add_row([request,need_evts,cpu_evt,output_eff,cpu_evt/output_eff,eff,init_time,int(cpu_need/1000.),r["GenType"]])
    if cpu_evt < 1000.:
        totals[0]+=r["NeededEvents"]
        totals[1]+=cpu_need
        totals[2]+=r["NeededEvents"]*output_eff
    gen_total[r["GenType"]]=gen_total.get(r["GenType"],0)+cpu_need/1000.
    gen_total_ev[r["GenType"]]=gen_total_ev.get(r["GenType"],0)+need_evts
    
myTable.add_row(["Total (no outlier)",totals[0]//1000,totals[1]*totals[2]/totals[0]/totals[0],totals[2]/totals[0],totals[1]/totals[
0],"","",int(totals[1]/1000.),""])

good_empties=[]
for request in empties:
    if request not in new_requests: good_empties.append(request)

print(good_empties)
print("Run so far: " + str(nFull))
print("Still to run: " + str(len(good_empties)))
print("New that could be to run: " + str(nEmpty-len(good_empties)))

print("Gen summary")

for gen,t in sorted(gen_total.items(), key = lambda x : x[1], reverse=False):
    print('%15s %10d %10d'%(gen,int(t),gen_total_ev[gen]))

print(myTable)
