#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
from configparser import ConfigParser
import pytak


class MySerializer(pytak.QueueWorker):
    """
    Defines how you process or generate your Cursor on Target Events.
    From there it adds the CoT Events to a queue for TX to a COT_URL.
    """

    async def handle_data(self, data):
        """Handle pre-CoT data, serialize to CoT Event, then puts on queue."""
        event = data
        await self.put_queue(event)

    async def run(self):
        """Run the loop for processing or generating pre-CoT data."""
        while True:
            data = gen_cot()
            await self.handle_data(data)
            await asyncio.sleep(20)


def gen_cot():
    """Generate CoT Event."""
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-h-A-M-A")  # insert your type of marker
    root.set("uid", "name_your_marker")
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set(
        "stale", pytak.cot_time(3600)
    )  # time difference in seconds from 'start' when stale initiates

    pt_attr = {
        "lat": "40.781789",  # set your lat (this loc points to Central Park NY)
        "lon": "-73.968698",  # set your long (this loc points to Central Park NY)
        "hae": "0",
        "ce": "10",
        "le": "10",
    }

    ET.SubElement(root, "point", attrib=pt_attr)

    return ET.tostring(root)


async def main():
    """Main definition of your program, sets config params and
        adds your serializer to the asyncio task list.
        """
    config = ConfigParser()
    config["mycottool"] = {
        "COT_URL": "tls://x.x.x.x:8089",
        "PYTAK_TLS_CLIENT_CERT": "c:\\Users\\admin\\Downloads\\meetup\\aws-pytak.pem",
        "PYTAK_TLS_CLIENT_KEY": "c:\\Users\\admin\\Downloads\\meetup\\aws-pytak.key",
        "PYTAK_TLS_CLIENT_PASSWORD": "password",
        "PYTAK_TLS_DONT_VERIFY": "1",
    }
    config = config["mycottool"]

    # Initializes worker queues and tasks.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add your serializer to the asyncio task list.
    clitool.add_tasks({MySerializer(clitool.tx_queue, config)})

    # Start all tasks.
    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())
