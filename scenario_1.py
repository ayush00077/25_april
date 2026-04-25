from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import requests

# 1. Define Settings class to load from .env
class Settings(BaseSettings):
    azure1_endpoint: str
    azure1_api_key: str

    class Config:
        env_file = ".env"

# Initialize settings
settings = Settings()

app = FastAPI(title="Retail Demand Forecast API (Azure Final)")

# 2. Use settings object for headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.azure1_api_key}"
}

# ---------------------------
# Request Schema
# ---------------------------
class DemandRequest(BaseModel):
    Date: str
    ProductID: str
    Category: str
    Region: str  
    Price: float
    Discount: float
    Holiday: int

# ---------------------------
# API Endpoint
# ---------------------------
@app.post("/predict-demand")
def predict_demand(request: DemandRequest):
    try:
        payload = {
            "Inputs": {
                "input1": [
                    {
                        "Date": request.Date,
                        "ProductID": request.ProductID,
                        "Category": request.Category,
                        "Region": request.Region, 
                        "Price": request.Price,
                        "Discount": request.Discount,
                        "Holiday": request.Holiday
                    }
                ]
            },
            "GlobalParameters": {}
        }

        # 3. Use settings.azure_endpoint here
        response = requests.post(
            settings.azure1_endpoint,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        result = response.json()
        prediction = result["Results"]["WebServiceOutput0"][0]

        demand = float(prediction.get("Scored Labels", 0))

        if demand > 180:
            drift_status = "High Demand (Possible Seasonal Spike)"
        elif demand < 30:
            drift_status = "Low Demand (Possible Drop)"
        else:
            drift_status = "Normal"

        return {
            "PredictedUnitsSold": demand,
            "DriftStatus": drift_status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))