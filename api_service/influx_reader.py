import os
from influxdb_client import InfluxDBClient

# Configuration
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "hems_data")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

def get_latest_status():
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r["_measurement"] == "energy_flow")
      |> last()
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    result = query_api.query(org=INFLUX_ORG, query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append(record.values)
    return results[0] if results else {}

def get_flow_timeseries(range_start="-24h"):
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {range_start})
      |> filter(fn: (r) => r["_measurement"] == "energy_flow")
      |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    '''
    result = query_api.query(org=INFLUX_ORG, query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append(record.values)
    return results

def get_soc_forecast(range_start="-1h", range_stop="24h"):
    # Read forecast_soc
    # Forecasts are in future, so range logic is tricky with Flux if we use relative start.
    # Usually we query start: now(), stop: now() + 24h
    # But Flux range requires start.
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {range_start}) 
      |> filter(fn: (r) => r["_measurement"] == "forecast_soc")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    '''
    result = query_api.query(org=INFLUX_ORG, query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append(record.values)
    return results
