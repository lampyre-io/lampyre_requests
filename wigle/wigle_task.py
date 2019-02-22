from lighthouse import *
from ontology import Attributes, City, Country, CityToCountry
from typing import Dict, List, Union, Any
import requests
import json
import os


# WiGLE API documentation: https://api.wigle.net/swagger
# Tutorial: https://lampyre.io/python-api-doc/task_tutorial/wigle_task.html
# Icons for custom objects provided by Icons8 https://icons8.com/


class WirelessNetworks(metaclass=Header):
    display_name = 'Wireless networks'

    SSID = Field('SSID', ValueType.String, system_name='ssid')
    TransId = Field('Trans ID', ValueType.String, system_name='transid')
    Name = Field('Name', ValueType.String, system_name='name')
    MacAddress = Field('MAC address', ValueType.String, system_name='netid')
    Encryption = Field('Encryption', ValueType.String, system_name='encryption')
    Trilat = Field('Trilat', ValueType.Float, system_name='trilat')
    Trilong = Field('Trilong', ValueType.Float, system_name='trilong')
    QoS = Field('Signal quality', ValueType.Integer, system_name='qos')
    Firsttime = Field('First time', ValueType.Datetime, system_name='firsttime')
    Lasttime = Field('Last time', ValueType.Datetime, system_name='lasttime')
    Lastupdt = Field('Last update', ValueType.Datetime, system_name='lastupdt')
    Housenumber = Field('House number', ValueType.String, system_name='housenumber')
    Road = Field('Road', ValueType.String, system_name='road')
    City = Field('City', ValueType.String, system_name='city')
    Region = Field('Region', ValueType.String, system_name='region')
    Country = Field('Country', ValueType.String, system_name='country')
    Type = Field('Type', ValueType.String, system_name='type')
    Comment = Field('Comment', ValueType.String, system_name='comment')
    WEP = Field('WEP', ValueType.String, system_name='wep')
    Channel = Field('Channel', ValueType.Integer, system_name='channel')
    BcnInterval = Field('Beacon interval', ValueType.Integer, system_name='bcninterval')
    Freenet = Field('Freenet', ValueType.String, system_name='freenet')
    DHCP = Field('DHCP', ValueType.String, system_name='dhcp')
    Paynet = Field('Paynet', ValueType.String, system_name='paynet')
    Userfound = Field('User found', ValueType.Boolean, system_name='userfound')


class WirelessStation(metaclass=Object):
    name = 'Wireless station'

    SSID = Attributes.str('SSID')
    MacAddress = Attributes.System.MacAddress
    Name = Attributes.System.Name
    TransId = Attributes.str('Trans ID')
    Encryption = Attributes.str('Encryption')
    QoS = Attributes.int('Signal quality')
    Type = Attributes.str('Type')
    Comment = Attributes.System.Comment
    WEP = Attributes.str('WEP')
    Channel = Attributes.int('Channel')
    BcnInterval = Attributes.int('Beacon interval')
    Freenet = Attributes.str('Freenet')
    DHCP = Attributes.str('DHCP')
    Paynet = Attributes.str('Paynet')
    GeoPoint = Attributes.System.GeoPoint

    Image = Utils.base64string(os.path.join('icons', 'icons8-router-32.png'))

    IdentAttrs = [MacAddress]
    CaptionAttrs = [SSID, MacAddress, Encryption]


class WirelessStationToCity(metaclass=Link):
    name = 'Wifi to city'

    Road = Attribute('Road', ValueType.String)

    CaptionAttrs = [Road]

    Begin = WirelessStation
    End = City


class WirelessNetworksSchema(metaclass=Schema):
    name = 'Networks'
    Header = WirelessNetworks

    station = SchemaObject(WirelessStation, mapping={
        WirelessStation.MacAddress: Header.MacAddress,
        WirelessStation.SSID: Header.SSID,
        WirelessStation.Name: Header.Name,
        WirelessStation.TransId: Header.TransId,
        WirelessStation.Encryption: Header.Encryption,
        WirelessStation.QoS: Header.QoS,
        WirelessStation.Type: Header.Type,
        WirelessStation.Comment: Header.Comment,
        WirelessStation.WEP: Header.WEP,
        WirelessStation.Channel: Header.Channel,
        WirelessStation.BcnInterval: Header.BcnInterval,
        WirelessStation.Freenet: Header.Freenet,
        WirelessStation.DHCP: Header.DHCP,
        WirelessStation.Paynet: Header.Paynet,
        WirelessStation.GeoPoint: [Header.Trilat, Header.Trilong]
    })

    city = SchemaObject(City, mapping={City.City: Header.City, City.Country: Header.Country})
    country = SchemaObject(Country, mapping={Country.Country: Header.Country})

    station_to_city = WirelessStationToCity.between(
        station, city,
        mapping={WirelessStationToCity.Road: Header.Road},
        conditions=[
            Condition(Header.MacAddress, Operations.NotEqual, ''),
            Condition(Header.City, Operations.NotEqual, '')
        ]
    )

    city_to_country = CityToCountry.between(
        city, country,
        mapping={},
        conditions=[
            Condition(Header.City, Operations.NotEqual, ''),
            Condition(Header.Country, Operations.NotEqual, '')
        ]
    )


class WigleWifiSearch(Task):
    def __init__(self):
        super().__init__()
        self.name = 'YOUR_USERNAME'
        self.token = 'YOUR_TOKEN'

    def get_id(self):
        return '7e9b9bde-3c0d-411a-ad32-a3ee992b0224'

    def get_display_name(self):
        return 'WiGLE WiFi search'

    def get_category(self):
        return 'Tutorial tasks'

    def get_description(self):
        return 'Search WiGLE wireless database'

    def get_headers(self):
        return HeaderCollection(
            WirelessNetworks
        )

    def get_enter_params(self):
        return EnterParamCollection(
            EnterParamField('ssid', 'SSID', ValueType.String,
                            description='Include only networks exactly matching the string network name'),
            EnterParamField('fuzzy', 'Fuzzy search', ValueType.Boolean,
                            description='Allow SSID wildcards ‘%’ (any string) and ‘_’ (any character)'),
            EnterParamField('area', 'Area', ValueType.String, geo_json=True)
        )

    def get_weight_function(self):
        return 'ssid'

    def get_schemas(self):
        return SchemaCollection(
            WirelessNetworksSchema
        )

    def get_gis_macros(self):
        return MacroCollection(
            Macro('Search WiFi in WiGLE', mapping_flags=[GisMappingFlags.Instances], schemas=self.get_schemas())
        )

    def execute(self, enter_params, result_writer, log_writer, temp_directory):
        if self.name == 'YOUR_USERNAME':
            log_writer.error('Please configure you WiGLE credentials in script')
        if not enter_params.ssid and not enter_params.area:
            log_writer.error('SSID or area required')

        request_params = self.create_request_params(enter_params.ssid, enter_params.fuzzy, enter_params.area)
        response = self.perform_search(request_params, log_writer)

        if not response.get('success'):
            log_writer.info('Nothing found')
            return

        total_results = response.get('totalResults')
        log_writer.info(f'Total results: {total_results}')

        results = response.get('results')
        for result in results:
            line = {field: result.get(field.system_name) for field in WirelessNetworks}
            result_writer.write_line(line)

    @staticmethod
    def create_request_params(ssid: str, fuzzy: bool, area: str) -> Dict[str, str]:
        """
        Creates HTTP request parameters from enter_params
        """
        if area:
            area_angles = json.loads(area, encoding='utf-8')['bbox']
            return {
                'longrange1': area_angles[0],
                'latrange1': area_angles[1],
                'longrange2': area_angles[2],
                'latrange2': area_angles[3],
                'variance': '0.001'
            }

        return {'ssid': ssid} if not fuzzy else {'ssidlike': ssid}

    def perform_search(self, params: Dict[str, str], log_writer: LogWriter) -> Dict[str, Any]:
        """
        Makes actual request to API
        """
        response = requests.get('https://api.wigle.net/api/v2/network/search',
                                params=params, auth=(self.name, self.token))

        if not response.ok:
            log_writer.info(f'Error performing request: ')
            log_writer.error(response.reason)

        return response.json()
