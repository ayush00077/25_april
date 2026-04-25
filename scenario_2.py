from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import requests

# 1. Define Settings class
class Settings(BaseSettings):
    azure2_endpoint: str
    azure2_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
app = FastAPI()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.azure2_api_key}"
}

class SensorData(BaseModel):
    MachineID: str
    Temperature: float
    Vibration: float
    Pressure: float
    Humidity: float
    Timestamp: str

@app.post("/predict-failure")
def predict_failure(data: SensorData):
    azure_payload = {
        "Inputs": {
            "input1": [
                {
                    "MachineID": data.MachineID,
                    "Temperature": data.Temperature,
                    "Vibration": data.Vibration,
                    "Pressure": data.Pressure,
                    "Humidity": data.Humidity,
                    "Timestamp": data.Timestamp
                }
            ]
        },
        "GlobalParameters": {}
    }

    try:
        response = requests.post(
            settings.azure2_endpoint,
            headers=headers,
            json=azure_payload
        )
        
        # Raise error for bad requests
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        result = response.json()

        # Handle response format
        if isinstance(result, list):
            prediction = result[0]
        elif "Results" in result:
            prediction = result["Results"]["WebServiceOutput0"][0]
        else:
            raise Exception(f"Unexpected response format: {result}")

        # Extract probability
        failure_prob = float(prediction.get("Scored Probabilities", 0))

        return {
            "failure_probability": failure_prob,
            "status": "High Risk" if failure_prob > 0.7 else "Normal"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))