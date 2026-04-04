import xml.dom.minidom
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from zoneinfo import ZoneInfo

import requests


def sanitize_xml_text(value):
    """Return text safe for XML 1.0 by stripping illegal control characters."""
    if value is None:
        return ""

    text = str(value)
    return "".join(
        ch for ch in text
        if (
            ch == "\t"
            or ch == "\n"
            or ch == "\r"
            or 0x20 <= ord(ch) <= 0xD7FF
            or 0xE000 <= ord(ch) <= 0xFFFD
            or 0x10000 <= ord(ch) <= 0x10FFFF
        )
    )


def fetch_epg_data(start_date, num_days):
    epg_data = {}
    for i in range(num_days - 1):
        date = start_date + timedelta(days=i)
        url = f"https://raibz.rai.it/lib/data_app_palinsesto.php?&tipo=tv&day={date.strftime('%Y-%m-%d')}&struct=sb&lang=de"
        response = requests.get(url)
        if not response.text.strip():
            continue
        data = response.json()
        epg_data[date.strftime('%Y-%m-%d')] = data['result']
    return epg_data


def convert_to_xmltv(epg_data, channel_name, icon_url=None, lang="de"):
    safe_channel_name = sanitize_xml_text(channel_name)
    safe_lang = sanitize_xml_text(lang)

    tv = Element("tv", source_info_url="https://raibz.rai.it", source_info_name="RAI.bz",
                 generator_info_name="XMLTV", generator_info_url="http://www.xmltv.org/")

    # Add channel information
    channel = SubElement(tv, "channel", id=safe_channel_name)
    display_name = SubElement(channel, "display-name", lang=safe_lang)
    display_name.text = safe_channel_name

    if icon_url:
        SubElement(channel, "icon", src=sanitize_xml_text(icon_url))

    for date, programs in epg_data.items():
        for program in programs:
            start_time = datetime.strptime(date + " " + program['ora'], "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Rome"))
            duration_minutes = int(program['durata'])
            stop_time = start_time + timedelta(seconds=duration_minutes)

            programme = SubElement(tv, "programme", start=start_time.strftime("%Y%m%d%H%M%S %z"),
                                   stop=stop_time.strftime("%Y%m%d%H%M%S %z"), channel=safe_channel_name)

            title = SubElement(programme, "title")
            title.text = sanitize_xml_text(program.get('titolo', ''))

            sub_title = SubElement(programme, "sub-title")
            sub_title.text = sanitize_xml_text(program.get('sottotitolo', ''))

            desc = SubElement(programme, "desc")
            desc.text = sanitize_xml_text(program.get('info', ''))

    return tostring(tv, encoding="utf-8")


def main():
    start_date = datetime.now().date()
    num_days = 10
    channel_name = "Rai Südtirol"
    icon_url = "https://i.imgur.com/GSsMRxE.png"
    epg_data = fetch_epg_data(start_date, num_days)
    xmltv_data = convert_to_xmltv(epg_data, channel_name, icon_url)

    # Parse the XML string into a DOM object
    dom = xml.dom.minidom.parseString(xmltv_data)

    # Pretty print the XML
    pretty_xmltv_data = dom.toprettyxml(encoding="utf-8", indent="  ").decode('utf-8')

    # Write the XMLTV data to a file
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xmltv_data)


if __name__ == "__main__":
    main()
