
import os
import pandas as pd
from influxdb_client import InfluxDBClient

# Reuse config
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "hems_data")

def inspect_pv_data():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()

    # Query for 2025-12-15 PV data
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: 2025-12-15T00:00:00Z, stop: 2025-12-16T00:00:00Z)
      |> filter(fn: (r) => r["_measurement"] == "energy_flow")
      |> filter(fn: (r) => r["_field"] == "pv_power_kw")
      |> sort(columns: ["_time"])
    '''
    
    print("Querying InfluxDB for PV data on 2025-12-15...")
    try:
        tables = query_api.query(query=query)
        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "time": record.get_time(), 
                    "value": record.get_value(),
                    "field": record.get_field()
                })
        
        if not data:
            print("No data found for 2025-01-01.")
            return

        df = pd.DataFrame(data)
        print("\n--- PV Data Inspection (First 24 hours) ---")
        print(df[["time", "value"]].to_string())
        
        # Check against CSV reference logic
        # CSV: 2025-01-01 08:00:00+00:00 -> 3.979
        # csv had 2025-01-01 09:00:00+00:00 -> 23.301
        
    except Exception as e:
        print(f"Query failed: {e}")

if __name__ == "__main__":
    inspect_pv_data()
