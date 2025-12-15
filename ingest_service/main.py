import asyncio
import os
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from influx_client import write_data

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
    # 1. Load CSV if exists
    csv_path = "mock_data.csv" # Expected to be mounted or copied
    if os.path.exists(csv_path):
        print("Loading initial mock data...")
        df = pd.read_csv(csv_path)

        # --- START KORREKTUR FÜR VERALTETE ZEITSTEMPEL ---
        # Das ist die kritische Änderung, um das 422 Problem zu beheben.
        
        # Berechne die Verschiebung: Wir bringen den ältesten CSV-Zeitstempel
        # auf 3 Tage vor UTC-Jetzt. Das garantiert, dass alle Daten innerhalb 
        # der 4-Wochen-Retention Policy liegen.


        # OLD: oldest_csv_time = pd.to_datetime(df['timestamp']).min()
        # NEU: Entferne die Zeitzonen-Information (macht das Objekt tz-naiv)
        oldest_csv_time = pd.to_datetime(df['timestamp']).min().tz_localize(None) 
        
        target_time = datetime.utcnow() - timedelta(hours=20)
        time_offset = target_time - oldest_csv_time
        
        # Wende den Zeit-Offset auf alle Zeitstempel in der DataFrame an
        df['timestamp'] = pd.to_datetime(df['timestamp']) + time_offset
        # --- ENDE KORREKTUR ---
        
        
        for _, row in df.iterrows():
            ts = pd.to_datetime(row['timestamp'])
            write_data(
                measurement="energy_flow",
                tags={"source": "csv_init"},
                fields={
                    "pv_power_kw": float(row['pv_power_kw']),
                    "consumption_power_kw": float(row['consumption_power_kw'])
                },
                timestamp=ts
            )
        print("Mock data loaded.")
    else:
        print(f"No mock data found at {csv_path}")

    # 2. Start simulation loop
    asyncio.create_task(run_simulation())

@app.get("/health", dependencies=[Depends(verify_token)])
def health_check():
    return {"status": "running", "service": "ingest_service"}
