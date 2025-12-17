
import os
from influxdb_client import InfluxDBClient

# Reuse config from influx_client or environment
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "hems_data")

def verify():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()

    print(f"Verifying data in bucket '{INFLUX_BUCKET}'...")

    # 1. Verify Consumption
    # Query for count of points in 2025
    query_consumption = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: 2025-01-01T00:00:00Z, stop: 2025-01-02T00:00:00Z)
      |> filter(fn: (r) => r["_measurement"] == "energy_flow")
      |> filter(fn: (r) => r["_field"] == "consumption_power_kw")
      |> count()
    '''
    try:
        result = query_api.query(query=query_consumption)
        if result:
            count = result[0].records[0].get_value()
            print(f"[PASS] Consumption data found for 2025-01-01. Count: {count}")
        else:
            print("[FAIL] No Consumption data found for 2025-01-01.")
    except Exception as e:
        print(f"[ERROR] Consumption query failed: {e}")

    # 2. Verify PV
    query_pv = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: 2025-01-01T00:00:00Z, stop: 2025-01-02T00:00:00Z)
      |> filter(fn: (r) => r["_measurement"] == "energy_flow")
      |> filter(fn: (r) => r["_field"] == "pv_power_kw")
      |> count()
    '''
    try:
        result = query_api.query(query=query_pv)
        if result:
            count = result[0].records[0].get_value()
            print(f"[PASS] PV data found for 2025-01-01. Count: {count}")
        else:
            print("[FAIL] No PV data found for 2025-01-01.")
    except Exception as e:
        print(f"[ERROR] PV query failed: {e}")

    # 3. Verify Market Prices
    query_price = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: 2025-01-01T00:00:00Z, stop: 2025-01-02T00:00:00Z)
      |> filter(fn: (r) => r["_measurement"] == "market_prices")
      |> filter(fn: (r) => r["_field"] == "price_eur_mwh")
      |> count()
    '''
    try:
        result = query_api.query(query=query_price)
        if result:
            count = result[0].records[0].get_value()
            print(f"[PASS] Market Price data found for 2025-01-01. Count: {count}")
        else:
            print("[FAIL] No Market Price data found for 2025-01-01.")
    except Exception as e:
        print(f"[ERROR] Market Price query failed: {e}")

if __name__ == "__main__":
    verify()
