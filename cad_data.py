import json
import uuid
import xml.etree.ElementTree as ET

import pytak

def convert_incident_to_cot(incident):
    """
    Converts a single incident dictionary from the JSON to a CoT Event XML string.
    """

    # Generate a unique UID for the event
    uid = f"GeoSafety-{incident.get('incident_number', uuid.uuid4())}"

    # Parse timestamps
    # Format in JSON appears to be "MM/DD/YYYY I:M:S PM" e.g., "12/17/2025 3:17:34 PM"
    # CoT requires ISO 8601: YYYY-MM-DDTHH:MM:SS.mmmmmmZ
    # time_format = "%m/%d/%Y %I:%M:%S %p"
    #
    # try:
    #     dispatch_time_str = incident.get('dispatch_date_utc', '')
    #     if dispatch_time_str:
    #         dt = datetime.strptime(dispatch_time_str, time_format)
    #     else:
    #         dt = datetime.utcnow()
    #
    #     # CoT time format
    #     cot_time = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    #     # Stale time (e.g., 20 minutes later)
    #     stale_time = (dt + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # except ValueError:
    #     # Fallback if parsing fails
    #     now = datetime.utcnow()
    #     cot_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    #     stale_time = (now + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Extract coordinates
    lat = incident.get('lat_coord', '0.0')
    lon = incident.get('long_coord', '0.0')

    # Determine type (Atom) based on priority or status
    # a-h-G is "Assumed Hostile Ground", a-f-G is "Assumed Friend Ground", a-u-G is "Assumed Unknown"
    # Using a-u-G (Unknown Ground) for general incidents, or specific mapping if desired
    cot_type = "a-u-G"

    # Create the root Event element
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("uid", uid)
    root.set("type", cot_type)
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(3600))
    root.set("how", "m-g")  # Machine generated

    # Create the point element
    point = ET.SubElement(root, "point")
    point.set("lat", lat)
    point.set("lon", lon)
    point.set("hae", "0.0")
    point.set("ce", "9999999.0")
    point.set("le", "9999999.0")

    # Create the detail element
    detail = ET.SubElement(root, "detail")

    # add usericon element
    usericon = ET.SubElement(detail, "usericon")
    usericon.set("iconsetpath", "6d781afb-89a6-4c07-b2b9-a89748b6a38f/Misc/Camp.png")

    # Add contact info
    contact = ET.SubElement(detail, "contact")
    code = incident.get('incident_type_code', 'INC')
    address = incident.get('incident_address', 'UNKNOWN')
    status = incident.get('incident_status', 'UNKNOWN').strip()
    call_sign = f"{code} | {status} | {address}"
    contact.set("callsign", call_sign)

    # Add remarks
    remarks = ET.SubElement(detail, "remarks")
    desc = incident.get('incident_type_description', '')
    address = incident.get('incident_address', '')
    dispatch_date = incident.get('dispatch_date_utc', '').strip()
    arrival_date = incident.get('arrival_date_utc', 'NO ARRIVAL').strip()
    report = f"{desc} at {address}\n\nSTATUS: {status}\nDISPATCHED: {dispatch_date}\nARRIVAL: {arrival_date}\n\n"

    # Extract comments list, defaulting to empty if missing
    comments_data = incident.get('Comments', [])
    formatted_comments = []

    for comment in comments_data:
        c_text = comment.get('comments_text', '').strip()
        c_date = comment.get('created_date_utc', '').strip()

        # Format: "Date: Comment Text"
        # Only add parts that exist to avoid empty spaces
        entry_parts = []
        if c_date:
            entry_parts.append(c_date)

        prefix = " ".join(entry_parts)

        if prefix:
            full_entry = f"{prefix}: {c_text}\n\n"
        else:
            full_entry = f"{c_text}\n\n"

        if full_entry:
            formatted_comments.append(full_entry)

    # Join all comments with a newline separator
    report += "".join(formatted_comments)
    remarks.text = report

    # Add custom group info if needed
    group = ET.SubElement(detail, "__group")
    if status == 'ACTIVE':
        group.set("name", "Orange")

    # Convert to string
    xml_str = ET.tostring(root, encoding='utf-8', method='xml')

    # Add XML declaration header manually as ET.tostring doesn't always include the standalone
    return b"<?xml version='1.0' standalone='yes'?>" + xml_str

if __name__ == "__main__":
    # Open the JSON file in read mode
    with open('sample.json', 'r') as file:
        # Load the JSON data into a Python dictionary
        data = json.load(file)

    # Now you can access the data
    # For example, printing the number of incidents found
    if "Incidents" in data:
        for incident in data["Incidents"]:
            cot_event = convert_incident_to_cot(incident)
            print(cot_event.decode('utf-8'))