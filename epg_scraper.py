import xml.dom.minidom
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring

import requests

def fetch_epg_data(start_date, num_days):
    epg_data = {}
    for i in range(num_days - 1):
        date = start_date + timedelta(days=i)
        url = f"https://raibz.rai.it/lib/data_app_palinsesto.php?&tipo=tv&day={date.strftime('%Y-%m-%d')}&struct=sb&lang=de"
        response = requests.get(url)
        if not response.text.strip():
            break
        data = response.json()
        epg_data[date.strftime('%Y-%m-%d')] = data['result']
    return epg_data

def convert_to_xmltv(epg_data, channel_name):
    tv = Element("tv", source_info_url="https://raibz.rai.it", source_info_name="RAI.bz",
                 generator_info_name="XMLTV", generator_info_url="http://www.xmltv.org/")

    for date, programs in epg_data.items():
        for program in programs:
            start_time = datetime.strptime(program['ora'], "%H:%M")
            duration_minutes = int(program['durata']) // 60
            stop_time = start_time + timedelta(minutes=duration_minutes)

            programme = SubElement(tv, "programme", start=start_time.strftime("%Y%m%d%H%M%S %z"),
                                   stop=stop_time.strftime("%Y%m%d%H%M%S %z"), channel=channel_name)

            title = SubElement(programme, "title")
            title.text = program['titolo']

            sub_title = SubElement(programme, "sub-title")
            sub_title.text = program['sottotitolo']

            desc = SubElement(programme, "desc")
            desc.text = program['info']

    return tostring(tv, encoding="utf-8")

def main():
    start_date = datetime.now().date()
    num_days = 10
    channel_name = "Rai Südtirol"
    epg_data = fetch_epg_data(start_date, num_days)
    xmltv_data = convert_to_xmltv(epg_data, channel_name)

    # Parse the XML string into a DOM object
    dom = xml.dom.minidom.parseString(xmltv_data)

    # Pretty print the XML
    pretty_xmltv_data = dom.toprettyxml(encoding="utf-8").decode('utf-8')

    # Write the XMLTV data to a file
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xmltv_data)

if __name__ == "__main__":
    main()
