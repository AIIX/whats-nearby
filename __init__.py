import re
import sys
import subprocess
import json
import requests
from wireless import Wireless
from adapt.intent import IntentBuilder
from os.path import join, dirname
from string import Template
from mycroft.skills.core import MycroftSkill
from mycroft.util import read_stripped_lines
from mycroft.util.log import getLogger
from mycroft.messagebus.message import Message

__author__ = 'aix'

LOGGER = getLogger(__name__)


class WhatsNearbySkill(MycroftSkill):
    def __init__(self):
        super(WhatsNearbySkill, self).__init__(name="WhatsNearbySkill")
        self.places_index = dirname(__file__) + '/places.json'
        self.app_id = self.settings['app_id']
        self.app_code = self.settings['app_code']


    def initialize(self):
        self.load_data_files(dirname(__file__))
         
        search_nearby_places_intent = IntentBuilder("NearbyPlaces").\
            require("SearchPlacesKeyword").build()
        self.register_intent(search_nearby_places_intent, self.handle_search_nearby_places_intent)

    def handle_search_nearby_places_intent(self, message):
        utterance = message.data.get('utterance').lower()
        utterance = utterance.replace(message.data.get('SearchPlacesKeyword'), '')
        searchString = utterance.replace(" ", "")
        
        method = "GET"
        url = "https://places.demo.api.here.com/places/v1/discover/explore"
        getcords = self.getLocation()
        getlat = getcords['location']['lat']
        getlong = getcords['location']['lng']
        cat = self.filterCat(searchString)
        data = "?at={0},{1}&cat={2}&app_id={3}&app_code={4}".format(getlat, getlong, cat, self.app_id, self.app_code)
        response = requests.request(method,url+data)
        self.speak("Following information was found");
        self.enclosure.ws.emit(Message("visualObject", {'desktop': {'data': response.text}}))
        
    def getLocation(self):
            
        postdata = {}
        ifaces = []
        flbmode = {
        "lacf": "false",
        "ipf": "true"
        }
        postdata['fallbacks'] = flbmode
        postdata['wifiAccessPoints'] = ifaces
        wireless = Wireless()
        wintf = wireless.interface()
        setwintf = 'iwlist {0} scan'.format(wintf) 
        wlist = subprocess.Popen([setwintf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=True) 

        for line in wlist.stdout:
            if "Address" in line:
                iface = {}
                key = line.split('Address: ')[1].strip()
                iface['macAddress'] = key
                ifaces.append(iface)
            if "dBm" in line:
                signal = line.split('level=')[1].strip().replace(' dBm', '')
                iface['signalStrength'] = int(signal)
            if "ESSID" in line:
                essid = line.split(':')[1].strip().replace('"', '')
            if "Frequency" in line:
                frequencyStr = line.split(':')[1].split(' GHz')[0]
                frequency = int(float(frequencyStr)*1000)
                channel = int(line.split('(Channel ')[1].replace(')',''))
                iface['channel'] = channel
                iface['frequency'] = frequency

        postdata['wifiAccessPoints'].sort(
            key=lambda x: x['signalStrength'], reverse=True)

        del postdata['wifiAccessPoints'][5:]
        
        url = 'https://location.services.mozilla.com/v1/geolocate?key=test'
        print json.dumps(postdata, sort_keys=True, indent=4, separators=(',', ': '))
        r = requests.post(url, data=json.dumps(postdata))
        getlocresult = json.loads(r.text)

        return getlocresult;
   
   
    def filterCat(self, keywords):
        keyword = keywords.lower()
        with open(self.places_index) as json_data:
            d = json.load(json_data)
            for key, value in d.items():
                if keyword in value:
                    return key
                else:
                    return keyword
        
        
    def stop(self):
        pass


def create_skill():
    return WhatsNearbySkill()
