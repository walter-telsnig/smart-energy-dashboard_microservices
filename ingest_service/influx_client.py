import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "hems_data")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_data(measurement: str, tags: dict, fields: dict, timestamp=None):
    point = Point(measurement)
    for k, v in tags.items():
        point = point.tag(k, v)
    for k, v in fields.items():
        point = point.field(k, v)
    if timestamp:
        point = point.time(timestamp, WritePrecision.NS)
    
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

def write_points(points: list):
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
