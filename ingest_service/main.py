import asyncio
import os
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from influxdb_client import Point, WritePrecision
from influx_client import write_data, write_points

app = FastAPI()

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretjwtkeyforlocaldev")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8003/token")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return username

# Simulation
async def run_simulation():
    while True:
        # Simulate data every 15 seconds
        # Generate random or pattern-based data
        import random
        pv = max(0, random.gauss(2.0, 1.0)) # Mock PV around 2kW
        consumption = max(0, random.gauss(1.5, 0.5)) # Mock Consumption
        
        write_data(
            measurement="energy_flow",
            tags={"source": "simulation"},
            fields={
                "pv_power_kw": float(pv),
                "consumption_power_kw": float(consumption)
            },
            timestamp=datetime.utcnow()
        )
        print(f"Simulated data written: PV={pv:.2f}, Cons={consumption:.2f}")
        await asyncio.sleep(15)

@app.on_event("startup")
async def startup_event():
    import glob
    print("Starting data ingestion from files (BATCH MODE)...")
    
    # Use dirname of the current file to locate data folder correctly
    base_path = os.path.join(os.path.dirname(__file__), "data")

    def process_file(f, measurement, tags, field_map):
        try:
            df = pd.read_csv(f)
            points = []
            for _, row in df.iterrows():
                p = Point(measurement)
                for k, v in tags.items():
                    p.tag(k, v)
                for csv_col, influx_field in field_map.items():
                    if csv_col in row:
                        val = float(row[csv_col])
                        p.field(influx_field, val)
                
                # Assume columns 'datetime' exists
                if 'datetime' in row:
                    ts = pd.to_datetime(row['datetime'])
                    p.time(ts, WritePrecision.NS)
                points.append(p)
            
            if points:
                write_points(points)
                print(f"Loaded {len(points)} points from {f}")
        except Exception as e:
            print(f"Error loading {f}: {e}")

    # 1. Consumption
    files = glob.glob(os.path.join(base_path, "consumption", "*.csv"))
    for f in files:
        process_file(f, "energy_flow", {"source": "file_consumption"}, {"consumption_kwh": "consumption_power_kw"})

    # 2. PV
    files = glob.glob(os.path.join(base_path, "pv", "*.csv"))
    for f in files:
        process_file(f, "energy_flow", {"source": "file_pv"}, {"production_kw": "pv_power_kw"})

    # 3. Market Prices
    files = glob.glob(os.path.join(base_path, "market", "*.csv"))
    for f in files:
        process_file(f, "market_prices", {"source": "file_market"}, {"price_eur_mwh": "price_eur_mwh"})

    print("Batch Data ingestion completed.")

    # Optional: Start simulation if needed for "live" feel beyond static data
    # asyncio.create_task(run_simulation())

@app.get("/health", dependencies=[Depends(verify_token)])
def health_check():
    return {"status": "running", "service": "ingest_service"}
