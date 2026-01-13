#!/usr/bin/env python3
import asyncio
import math
import time
import uuid
import xml.etree.ElementTree as ET
from configparser import ConfigParser

import pytak


# --- Simulation parameters (Troy, MI) ---
START_LAT = 42.6064
START_LON = -83.1498

UPDATE_SECS = 1.0           # send rate
GROUND_SPEED_MPS = 15.0     # ~29 knots
COURSE_DEG = 90.0           # due east
ALT_HAE_M = 120.0           # height above ellipsoid


def meters_to_deg_lon(meters: float, lat_deg: float) -> float:
    """
    Convert east/west meters to degrees longitude at a given latitude.
    """
    lat_rad = math.radians(lat_deg)
    meters_per_deg_lon = 111_320.0 * math.cos(lat_rad)
    if meters_per_deg_lon == 0:
        return 0.0
    return meters / meters_per_deg_lon


class DroneRemoteIDSerializer(pytak.QueueWorker):
    """
    Generates and transmits CoT events representing a moving drone,
    including a Remote ID-like payload inside <detail>.
    """

    def __init__(self, queue, config):
        super().__init__(queue, config)

        # Stable identifiers for this "drone"
        self.drone_uuid = str(uuid.uuid4())
        self.ua_serial = f"UAS-{self.drone_uuid[:12].upper()}"  # simulated UAS ID / serial
        self.callsign = "DRONE-REMOTEID"

        # State
        self.lat = START_LAT
        self.lon = START_LON
        self.start_monotonic = time.monotonic()

    async def run(self):
        while True:
            cot = self.gen_cot_event()
            await self.put_queue(cot)
            await asyncio.sleep(UPDATE_SECS)

    def gen_cot_event(self) -> bytes:
        # How far have we traveled east since start?
        elapsed = time.monotonic() - self.start_monotonic
        east_meters = GROUND_SPEED_MPS * elapsed
        self.lon = START_LON + meters_to_deg_lon(east_meters, START_LAT)

        # --- CoT root ---
        root = ET.Element("event")
        root.set("version", "2.0")

        # Common CoT type for UAV/air track; adjust if your TAK conventions differ:
        # "a-f-A-M-F-Q" is often used for friendly aircraft (UAV fits many setups).
        root.set("type", "a-f-A-M-F-Q")

        # Use a stable UID so TAK shows a single moving track
        root.set("uid", self.ua_serial)

        root.set("how", "m-g")
        root.set("time", pytak.cot_time())
        root.set("start", pytak.cot_time())
        root.set("stale", pytak.cot_time(int(UPDATE_SECS * 6)))  # stale a few updates out

        # --- Point ---
        pt_attr = {
            "lat": f"{self.lat:.7f}",
            "lon": f"{self.lon:.7f}",
            "hae": f"{ALT_HAE_M:.1f}",
            "ce": "10",
            "le": "10",
        }
        ET.SubElement(root, "point", attrib=pt_attr)

        # --- Detail: callsign + track + "Remote ID" payload ---
        detail = ET.SubElement(root, "detail")

        # TAK contact/callsign
        ET.SubElement(detail, "contact", attrib={"callsign": self.callsign})

        # Track vector
        ET.SubElement(
            detail,
            "track",
            attrib={
                "course": f"{COURSE_DEG:.1f}",
                "speed": f"{GROUND_SPEED_MPS:.2f}",  # meters/sec
            },
        )

        # Remote ID-like payload (custom element; TAK will carry it even if it doesn't render it)
        # You can reshape these fields to match whatever your downstream expects.
        rid = ET.SubElement(
            detail,
            "remoteid",
            attrib={
                "standard": "simulated",
                "uas_id": self.ua_serial,
                "msg_type": "basic_id+location",
            },
        )
        ET.SubElement(rid, "location", attrib={
            "lat": f"{self.lat:.7f}",
            "lon": f"{self.lon:.7f}",
            "alt_hae_m": f"{ALT_HAE_M:.1f}",
            "speed_mps": f"{GROUND_SPEED_MPS:.2f}",
            "heading_deg": f"{COURSE_DEG:.1f}",
        })
        ET.SubElement(rid, "timestamp", attrib={"iso8601": pytak.cot_time()})

        # Optional human-readable summary
        ET.SubElement(
            detail,
            "remarks"
        ).text = f"RemoteID sim: {self.ua_serial} @ {self.lat:.6f},{self.lon:.6f} hdg={COURSE_DEG:.0f} spd={GROUND_SPEED_MPS:.1f}m/s"

        return ET.tostring(root)

#
async def main():
    config = ConfigParser()
    config["drone_remoteid"] = {
        "COT_URL": "tls://x.x.x.x:8089",
        "PYTAK_TLS_CLIENT_CERT": r"c:\Users\admin\Downloads\meetup\aws-pytak.pem",
        "PYTAK_TLS_CLIENT_KEY": r"c:\Users\admin\Downloads\meetup\aws-pytak.key",
        "PYTAK_TLS_CLIENT_PASSWORD": "password",
        "PYTAK_TLS_DONT_VERIFY": "1",
    }
    cfg = config["drone_remoteid"]

    clitool = pytak.CLITool(cfg)
    await clitool.setup()

    clitool.add_tasks({DroneRemoteIDSerializer(clitool.tx_queue, cfg)})
    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())
