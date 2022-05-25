import xml.etree.ElementTree as ET

def parse_xml(response):
    try:
        xml = ET.XML(response)
        code = xml.find('returncode').text
        if code == 'SUCCESS':
            return xml
        else:
            raise
    except:
        return None


def xml_to_json(xml):
    result = {}
    for x in xml:
        result[x.tag] = x.text
    return result