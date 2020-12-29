import asyncio
from cloudevents.http import CloudEvent, to_structured
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

import bme680
import time

sensor = bme680.BME680()

print("initializing sensor")
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)

# Disable gas measurement - not very reliable.
sensor.set_gas_status(bme680.DISABLE_GAS_MEAS)
#sensor.set_gas_heater_temperature(320)
#sensor.set_gas_heater_duration(150)
#sensor.select_gas_heater_profile(0)

async def run(loop):
    nc = NATS()
	
    await nc.connect("nats.wellorder.net:4222", loop=loop)
    while True: 
        # read items from BMP680
        if sensor.get_sensor_data(): 
            # convert to kelvin
            temp = sensor.data.temperature + 273.15
            press = sensor.data.pressure
            humid = sensor.data.humidity
            # make cloudevent
            attributes = {
                "type": "com.wellorder.iot.indoorenv",
                "source": "https://pentax.wellorder.net/iot/bme680",
                "datacontenttype": "application/json"
            }
            data = {"loc": "office.rpi-cluster",
                    "dt": time.time(),
                    "temp": temp,
                    "pressure": press,
                    "humidity": humid,
                    "sensorModel": "BME680"}
            event = CloudEvent(attributes, data)
            header, body = to_structured(event)
            await nc.publish("iot.indoorenv", body)
        # Exit
        await asyncio.sleep(1)
    # Terminate connection to NATS.
    await nc.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()
