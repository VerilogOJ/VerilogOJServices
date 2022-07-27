from fastapi import FastAPI, Body
from typing import Union, List

app = FastAPI()

from pydantic import BaseModel


class ServiceRequest(BaseModel):
    request: str


class ServiceResponse(BaseModel):
    response: str


@app.post(path="/", response_model=ServiceResponse)
def read_root(service_request: ServiceRequest):
    return {"response": "response"}
