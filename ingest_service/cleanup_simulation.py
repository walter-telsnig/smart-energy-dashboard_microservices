
import os
from influxdb_client import InfluxDBClient

# Reuse config
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "hems_data")

def delete_simulation_data():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    delete_api = client.delete_api()
    
    # Delete all simulation data from 2023 to 2030 (broad range)
    start = "2023-01-01T00:00:00Z"
    stop = "2030-01-01T00:00:00Z"
    predicate = '_measurement="energy_flow" AND source="simulation"'
    
    print(f"Deleting data with predicate: {predicate}...")
    try:
        delete_api.delete(start, stop, predicate, bucket=INFLUX_BUCKET, org=INFLUX_ORG)
        print("Deletion request sent.")
    except Exception as e:
        print(f"Deletion failed: {e}")

if __name__ == "__main__":
    delete_simulation_data()
