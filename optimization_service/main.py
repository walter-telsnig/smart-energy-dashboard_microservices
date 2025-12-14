import os
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from influx_client import write_forecast

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

@app.get("/forecast/soc_profile", dependencies=[Depends(verify_token)])
def generate_soc_forecast():
    """
    Generates a 24h SoC forecast (15m resolution) and writes to InfluxDB.
    Returns the generated profile.
    """
    now = datetime.utcnow()
    # Align to next 15m
    start_time = now.replace(second=0, microsecond=0)
    minutes = start_time.minute
    remainder = minutes % 15
    start_time += timedelta(minutes=(15 - remainder))

    forecast_points = []
    
    # Simple simulation logic:
    # Start SoC = 50%
    # PV bell curve during day, Consumption pseudo-random
    # SoC change = (PV - Cons) * Factor
    
    current_soc = 50.0
    capacity_kwh = 10.0 # 10kWh battery
    
    for i in range(4 * 24): # 96 points (24h * 4 quarters)
        forecast_time = start_time + timedelta(minutes=15 * i)
        hour = forecast_time.hour
        
        # Mock PV: Peak at 12:00, zero at night
        if 6 <= hour <= 18:
            pv_gen = max(0, 5.0 * (1 - abs(hour - 12) / 6)) # Simple triangle shape
        else:
            pv_gen = 0.0
            
        consumption = random.uniform(0.5, 2.0)
        
        net_power = pv_gen - consumption # kW
        # Energy in 15m = Power * 0.25h
        energy_change = net_power * 0.25
        
        # Update SoC
        soc_change_percent = (energy_change / capacity_kwh) * 100
        current_soc = max(0, min(100, current_soc + soc_change_percent))
        
        # Write to InfluxDB "forecast_soc"
        write_forecast(
            measurement="forecast_soc",
            tags={"algorithm": "simple_heuristic"},
            fields={"soc_percent": float(current_soc)},
            timestamp=forecast_time
        )
        
        forecast_points.append({
            "timestamp": forecast_time.isoformat(),
            "soc": current_soc,
            "pv_forecast": pv_gen,
            "load_forecast": consumption
        })
        
    return {"message": "Forecast generated and stored", "data": forecast_points}
