import re
import sys
import time
import json
from netmiko import ConnectHandler
from netaddr import *


input = "here some number AP12DB.43DE.78E8 for testing"
matches = re.findall(r'\bAP[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}.[0-9A-Fa-f]{4}\b', input)
print(matches)


#AP1006.ED4D.32D0


#Load Config-File
with open('/etc/config.json') as config_file:
	config = json.load(config_file)


def collect_cdp_nei():
    jkpitapconfpoe = {
        'device_type': 'cisco_ios',
        'host':   config['SWITCH_AP'],
        'username': config['SWITCHUSER'],
        'password': config['SWITCHPASS'],
        'port' : config['SWITCH_PORT'],          # optional, defaults to 22
        'secret': config['SWITCHPASS'],     # optional, defaults to ''
    }


    with ConnectHandler(**jkpitapconfpoe) as net_connect:
        #Hämtsa information från switchen, antal anslutna AP:s och vad dom heter bla.
        cdpOutput = net_connect.send_command('sh cdp neig',use_textfsm=True) 
        
    
    return(cdpOutput)

def getCdpNei(startAntal):

    


    #Number Of AP:s Connected
    cdps= int(startAntal)
    i=0
    maxtime = 10 # *30sekunder = 300sekunder
    t = 0

    while i != cdps:
        cdpNei = collect_cdp_nei()
        
        i=0
        for line in cdpNei:
            #if line['platform'] == config['AP_PLATFORM']:
            if line['platform'].startswith(config['AP_PLATFORM_PRE']) and (line['platform'].endswith(config['AP_PLATFORM_SUF1']) or line['platform'].endswith(config['AP_PLATFORM_SUF2'])):
                i=i+1
                
        print(i)
        #socketio.emit('test_response',{'data': str(i) + ' AP:s connected of ' + str(cdps) })
        t=t+1
        if t == maxtime:
            print ('Maximum wait-time reached, please check your AP:s and re-run the script.')
            #socketio.emit('test_response',{'data': 'Maximum wait-time reached, please check your AP:s and re-run the script.'})
            sys.exit(2)
        if i != cdps:
            time.sleep(30) #Wait for all AP:s to connect.

    cleanDict = []
    for line in cdpNei:
        #if line['platform'] == config['AP_PLATFORM']:
        if line['platform'].startswith(config['AP_PLATFORM_PRE']) and (line['platform'].endswith(config['AP_PLATFORM_SUF1']) or line['platform'].endswith(config['AP_PLATFORM_SUF2'])):
            temp = line['local_interface'][8:]
            line['local_interface'] = int(temp)
            cleanDict.append(line)

    newlist = sorted(cleanDict, key=lambda d: int(d['local_interface']))

    print(newlist)

 
getCdpNei(3)