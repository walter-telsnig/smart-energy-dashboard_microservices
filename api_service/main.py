import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from influx_reader import get_latest_status, get_flow_timeseries, get_soc_forecast

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

@app.get("/data/current_status", dependencies=[Depends(verify_token)])
def current_status():
    data = get_latest_status()
    # Serialize InfluxDB record to JSON
    # Flux returns dictionary with keys including '_time', 'consumption_power_kw', 'pv_power_kw'
    return clean_influx_data(data)

@app.get("/data/flow/timeseries", dependencies=[Depends(verify_token)])
def flow_timeseries():
    data = get_flow_timeseries(range_start="-24h")
    return [clean_influx_data(record) for record in data]

@app.get("/data/soc/timeseries", dependencies=[Depends(verify_token)])
def soc_timeseries():
    # Fetch forecast data
    # Note: OptimizationService creates forecast.
    data = get_soc_forecast(range_start="-1h") # Fetch recently generated forecasts
    return [clean_influx_data(record) for record in data]

def clean_influx_data(record):
    """
    Cleans InfluxDB record dictionary for JSON response.
    Removes internal keys like _start, _stop, result, table
    """
    if not record:
        return {}
    clean = {}
    for k, v in record.items():
        if not k.startswith("_") and k not in ["result", "table"]:
            clean[k] = v
        elif k == "_time":
            clean["timestamp"] = v.isoformat() if hasattr(v, 'isoformat') else v
    return clean
