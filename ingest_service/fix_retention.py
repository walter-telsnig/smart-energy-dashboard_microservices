
import os
from influxdb_client import InfluxDBClient

# Reuse config
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "myorg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "hems_data")

def fix_retention():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    buckets_api = client.buckets_api()
    
    print(f"Searching for bucket '{INFLUX_BUCKET}'...")
    bucket = buckets_api.find_bucket_by_name(INFLUX_BUCKET)
    
    if bucket:
        print(f"Found bucket: {bucket.name}, Retention Rules: {bucket.retention_rules}")
        # Update to generic "0" (infinite) or e.g. 5 years
        # Typically rule: every_seconds=... 
        # 0 means infinite usually? Or we set a very large number.
        # 10 years = 10 * 365 * 24 * 3600 = 315360000 s
        
        # We need to construct the update object properly depending on SDK version
        # Usually it's bucket.retention_rules = [...]
        # But update_bucket takes bucket arg.
        
        bucket.retention_rules[0].every_seconds = 315360000 # 10 years
        
        print(f"Updating retention to 10 years...")
        buckets_api.update_bucket(bucket)
        print("Bucket updated.")
        
        # Verify
        bucket_updated = buckets_api.find_bucket_by_name(INFLUX_BUCKET)
        print(f"New Retention Rules: {bucket_updated.retention_rules}")
    else:
        print(f"Bucket '{INFLUX_BUCKET}' not found.")

if __name__ == "__main__":
    fix_retention()
