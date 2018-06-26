"""
WhatsNearby Mycroft Skill.
"""
import re
import sys
import subprocess
import json
import requests
import pyric            
import pyric.pyw as pyw
from adapt.intent import IntentBuilder
from os.path import join, dirname
from string import Template
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util import read_stripped_lines
from mycroft.util.log import getLogger
from mycroft.messagebus.message import Message

__author__ = 'aix'

LOGGER = getLogger(__name__)


class WhatsNearbySkill(MycroftSkill):
    """
    WhatsNearby Skill Class.
    """    
    def __init__(self):
        """
        Initialization.
        """
        super(WhatsNearbySkill, self).__init__(name="WhatsNearbySkill")
        self.places_index = dirname(__file__) + '/places.json'
        self.app_id = self.settings['app_id']
        self.app_code = self.settings['app_code']
         
    @intent_handler(IntentBuilder("NearbyPlaces").require("SearchPlacesKeyword").build())
    def handle_search_nearby_places_intent(self, message):
        """
        Handle Search Nearby Keyword
        """
        utterance = message.data.get('utterance').lower()
        utterance = utterance.replace(message.data.get('SearchPlacesKeyword'), '')
        searchString = utterance.replace(" ", "")
        
        method = "GET"
        url = "https://places.demo.api.here.com/places/v1/discover/explore"
        getcords = self.getLocation()
        getlat = getcords['location']['lat']
        getlong = getcords['location']['lng']
        cat = self.filterCat(searchString)
        sendappid = str(self.app_id)
        sendappcode = str(self.app_code)
        data = "?at={0},{1}&cat={2}&app_id={3}&app_code={4}".format(getlat, getlong, cat, self.app_id, self.app_code)
        LOGGER.info(url+data)
        response = requests.request(method,url+data)
        if cat is not False:
            self.speak("Following information was found");
            self.enclosure.ws.emit(Message("placesObject", {'desktop': {'data': response.text, 'locallat': getlat, 'locallong': getlong, 'appid': sendappid, 'appcode': sendappcode}}))
        
    def getLocation(self):
        """
        Get location from Wlan and WifiAccessPoints for Mozilla Location Services
        """    
        postdata = {}
        ifaces = []
        flbmode = {
        "lacf": "false",
        "ipf": "true"
        }
        postdata['fallbacks'] = flbmode
        postdata['wifiAccessPoints'] = ifaces
        wintf = pyw.winterfaces()
        selectintf = wintf[0]
        setwintf = 'iwlist {0} scan'.format(selectintf) 
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
                #channel = int(line.split('(Channel ')[1].replace(')',''))
                #iface['channel'] = channel
                iface['frequency'] = frequency

        postdata['wifiAccessPoints'].sort(
            key=lambda x: x['signalStrength'], reverse=True)

        del postdata['wifiAccessPoints'][5:]
        
        url = 'https://location.services.mozilla.com/v1/geolocate?key=test'
        r = requests.post(url, data=json.dumps(postdata))
        getlocresult = json.loads(r.text)

        return getlocresult;
   
   
    def filterCat(self, keywords):
        """
        Filter location type
        """    
        keyword = keywords.lower()
        with open(self.places_index) as json_data:
            d = json.load(json_data)
            if keyword in d["eat-drink"]:
                return "eat-drink"
            elif keyword in d["shopping"]:
                return "shopping"
            elif keyword in d["toilet-rest-area"]:
                return "toilet-rest-area"
            elif keyword in d["natural-geographical"]:
                return "natural-geographical"
            elif keyword in d["petrol-station"]:
                return "petrol-station"
            elif keyword in d["hospital-health-care-facility"]:
                return "hospital-health-care-facility"
            elif keyword in d["atm-bank-exchange"]:
                return "atm-bank-exchange"
            elif keyword in d["administrative-areas-buildings"]:
                return "administrative-areas-buildings"
            elif keyword in d["going-out"]:
                return "going-out"
            elif keyword in d["sights-museums"]:
                return "sights-museums"
            elif keyword in d["accommodation"]:
                return "accommodation"
            elif keyword in d["transport"]:
                return "transport"
            else:
                self.speak("Could not find {0}".format(keyword))
                return False
        
        
    def stop(self):
        """
        Mycroft Stop Function
        """
        pass


def create_skill():
    """
    Mycroft Create Skill Function
    """
    return WhatsNearbySkill()
