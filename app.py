from flask import Flask, render_template, session, url_for
from flask_socketio import SocketIO, emit
import logging
import sys
import time
import json
from netmiko import ConnectHandler
from netaddr import *



#Logging config:
logging.basicConfig(level=logging.WARNING, filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#Load Config-File
with open('/etc/config.json') as config_file:
	config = json.load(config_file)




# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)



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

def getCdpNei(startSuffix, startApNum, startLocation, startAntal):

    


    #Number Of AP:s Connected
    cdps= int(startAntal)
    i=0
    maxtime = 10 # *30sekunder = 300sekunder
    t = 0

    while i != cdps:
        cdpNei = collect_cdp_nei()
        
        i=0
        for line in cdpNei:
            if line['platform'] == config['AP_PLATFORM']:
                i=i+1
        print(i)
        socketio.emit('test_response',{'data': str(i) + ' AP:s connected of ' + str(cdps) })
        t=t+1
        if t == maxtime:
            print ('Maximum wait-time reached, please check your AP:s and re-run the script.')
            socketio.emit('test_response',{'data': 'Maximum wait-time reached, please check your AP:s and re-run the script.'})
            sys.exit(2)
        if i != cdps:
            time.sleep(30) #Wait for all AP:s to connect.

    cleanDict = []
    for line in cdpNei:
        if line['platform'] == config['AP_PLATFORM']:
            temp = line['local_interface'][8:]
            line['local_interface'] = int(temp)
            cleanDict.append(line)

    newlist = sorted(cleanDict, key=lambda d: int(d['local_interface']))

 
    
    apNum = int(startApNum)
    location = startLocation
    suffix = startSuffix

    with ConnectHandler(ip = config['firstWlcIp'],
                        port = config['WLC_PORT'],
                        username = config['WLCUSER'],
                        password = config['WLCPASS'],
                        device_type = config['WLC_DEVICE_TYPE']) as wlc_connect:


        
        #Set All Connected AP to False
        for line in newlist:
            line['capability'] = 'False'
            print(line)
        
        #Check if  ALL AP:s is connected to WLC:
        allApConnected = False
        while not allApConnected:
            for line in newlist:


                wlc_show_commands = 'show ap config general' + line['neighbor']
                output = wlc_connect.send_command_w_enter(wlc_show_commands)

                if output.startswith( 'Cisco AP name is invalid' ):
                    print('AP ' + line['neighbor'] + ' NOT connected.')
                    socketio.emit('test_response',{'data': 'AP ' + line['neighbor'] + ' NOT connected.'})
                    line['capability'] = 'False'
                else:
                    print('AP ' + line['neighbor'] + ' connected')
                    socketio.emit('test_response',{'data': 'AP ' + line['neighbor'] + ' connected.'})
                    line['capability'] = 'True'  


            if all (d['capability'] == 'True' for d in newlist):
                print('ALL AP:S Connected!')
                socketio.emit('test_response',{'data': 'All AP:s connected!!'})
                allApConnected = True
            else:
                print('NOT ALL AP:s ARE CONNECTED. WAITING!')
                socketio.emit('test_response',{'data': 'Not all the AP:s are connected. Please wait...'})

        #Configure AP:s 
        for line in newlist:

                a_str = ('%03d' % apNum)
                apName = suffix + str(a_str)
                apNum = apNum + 1

                wlc_config_commands = ('config ap name' + ' ' + apName + ' ' + line['neighbor'],
                                'config ap location' + ' ' + location + ' ' +  apName,
                                'config ap primary-base' + ' ' + config['firstWlc'] + ' ' + apName + ' ' + config['firstWlcIp'],
                                'config ap secondary-base' + ' ' + config['secondWlc'] + ' ' + apName + ' ' + config['secondWlcIp']
                                )

                for wlc_config_command in wlc_config_commands:
                    print ('WLC input: ' + wlc_config_command)
                    socketio.emit('test_response',{'data': 'WLC input: ' + wlc_config_command})
                    output = wlc_connect.send_command_w_enter(wlc_config_command)
                    print('WLC Output: ' + output)
                    socketio.emit('test_response',{'data': 'WLC output: ' + output})
   

def background_job(data):
    """Example of how to send server generated events to clients."""
    
    print(f"AP Prefix: {data['appre']}")
    print(f"Antal AP: {data['antap']}")
    print(f"AP Startnummer: {data['apstart']}")
    print(f"AP Location: {data['aploc']}")
    startPrefix = str(data['appre'])
    startAntal= str(data['antap'])
    startApNum= str(data['apstart'])
    startLocation = str(data['aploc'])
    
    getCdpNei(startPrefix, startApNum, startLocation, startAntal)
    
    socketio.emit('enable_btn',{'data': 'Done! Script is ready for next batch of AP:S'})



@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/help')
def help():
    return render_template('help.html')

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})

# Receive the test request from client and send back a test response
@socketio.on('test_message')
def handle_message(data):
    print('received message: ' + str(data))
    emit('test_response', {'data': 'Test response sent'})
    background_job(data)
    emit('test_response', {'data': 'Connected', 'count': 300})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)