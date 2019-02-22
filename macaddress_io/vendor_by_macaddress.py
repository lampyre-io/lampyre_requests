from lighthouse import *
from ontology import Attributes
from requests import Session
from typing import Dict, Any
import os


# macaddress.io API documentation: https://macaddress.io/api/documentation/making-requests
# Tutorial: https://lampyre.io/python-api-doc/api_explained/schemas.html
# Icons for custom objects provided by Icons8 https://icons8.com/


class VendorsHeader(metaclass=Header):
    display_name = 'Vendors'

    MacAddress = Field('MAC address', ValueType.String)
    Oui = Field('OUI', ValueType.String)
    IsPrivate = Field('Is private', ValueType.Boolean)
    CompanyName = Field('Company name', ValueType.String)
    CompanyAddress = Field('Company address', ValueType.String)
    CountryCode = Field('Country code', ValueType.String)


class Vendor(metaclass=Object):
    Oui = Attribute('OUI', ValueType.String)  # unique vendor number
    IsPrivate = Attribute('Is private', ValueType.Boolean)
    CompanyName = Attribute('Company name', ValueType.String)
    CompanyAddress = Attribute('Company address', ValueType.String)

    IdentAttrs = [Oui]
    CaptionAttrs = [CompanyName]

    Image = Utils.base64string(os.path.join('icons', 'icons8-factory-48.png'))


class MacAddress(metaclass=Object):
    name = 'Mac address'

    MacAddress = Attributes.System.MacAddress

    IdentAttrs = [MacAddress]
    CaptionAttrs = [MacAddress]

    Image = Utils.base64string(os.path.join('icons', 'icons8-electronics-48.png'))


class VendorToMacAddress(metaclass=Link):
    name = 'Vendor of hardware'

    CompanyName = Attribute('Company name', ValueType.String)

    Begin = Vendor
    End = MacAddress


class VendorsSchema(metaclass=Schema):
    name = 'Hardware vendors'
    Header = VendorsHeader

    vendor = SchemaObject(Vendor, mapping={
        Vendor.Oui: Header.Oui, Vendor.IsPrivate: Header.IsPrivate,
        Vendor.CompanyName: Header.CompanyName, Vendor.CompanyAddress: Header.CompanyAddress,
    })

    macaddress = SchemaObject(MacAddress, mapping={MacAddress.MacAddress: Header.MacAddress})

    connection = SchemaLink(VendorToMacAddress, mapping={VendorToMacAddress.CompanyName: Header.CompanyName},
                            begin=vendor, end=macaddress,
                            conditions=[
                                # Condition(Header.CompanyName, Operations.NotEqual, ''),
                                # Condition(Header.MacAddress, Operations.StartsWith, '00:1A:A9')
                            ],
                            condition_union_mode=UnionMode.And,
                            condition_ignore_case=True
                            )


class MacVendorsTask(Task):
    def __init__(self):
        super().__init__()
        self.token = 'YOUR_API_TOKEN'

    def get_id(self):
        return '56375f22-d91c-4693-8e5b-30f01edad531'

    def get_display_name(self):
        return 'Vendor by MAC address'

    def get_category(self):
        return 'Tutorial tasks'

    def get_description(self):
        return 'Search hardware vendor by MAC address via https://macaddress.io'

    def get_headers(self):
        return HeaderCollection(VendorsHeader)

    def get_enter_params(self):
        return EnterParamCollection(
            EnterParamField('addresses', 'MAC addresses', ValueType.String, is_array=True, required=True,
                            value_sources=[ValueSource(Attributes.System.MacAddress)])
        )

    def get_weight_function(self):
        return super().get_weight_function()

    def get_schemas(self):
        return VendorsSchema

    def get_graph_macros(self):
        return MacroCollection(
            # this will allow to run this task as macro
            Macro('Vendor lookup', mapping_flags=[GraphMappingFlags.Completely], schemas=[VendorsSchema])
        )

    def execute(self, enter_params, result_writer, log_writer, temp_directory):
        session = Session()  # it is recommended to make many requests to one resource within one session
        session.headers.update({'X-Authentication-Token': self.token})

        for macaddress in set(enter_params.addresses):
            try:
                response = self.make_request(session, macaddress)
                vendor_details = response.get('vendorDetails', {})

                line = VendorsHeader.create_empty()

                line[VendorsHeader.MacAddress] = macaddress
                line[VendorsHeader.Oui] = vendor_details.get('oui')
                line[VendorsHeader.IsPrivate] = vendor_details.get('isPrivate')
                line[VendorsHeader.CompanyName] = vendor_details.get('companyName')
                line[VendorsHeader.CompanyAddress] = vendor_details.get('companyAddress')
                line[VendorsHeader.CountryCode] = vendor_details.get('countryCode')

                result_writer.write_line(line, header_class=VendorsHeader)

            except Exception as e:
                log_writer.info('Error requesting address: ' + macaddress)
                log_writer.info(e)

    def make_request(self, session: Session, macaddress: str) -> Dict[str, Dict[str, Any]]:
        params = {'output': 'json', 'search': macaddress}
        return session.get('https://api.macaddress.io/v1', params=params).json()
