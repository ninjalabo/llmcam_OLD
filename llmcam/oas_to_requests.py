# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/oas_to_requests.ipynb.

# %% auto 0
__all__ = ['BASE_URL', 'oas', 'get_request_body_from_schema', 'generate_request_by_operation_id']

# %% ../nbs/oas_to_requests.ipynb 3
import requests
from openapi_schema_pydantic import OpenAPI
import json
import yaml

# %% ../nbs/oas_to_requests.ipynb 5
BASE_URL = "https://petstore3.swagger.io/api/v3"

# Load and parse the OAS file
with open("openapi.json.3") as f:
    spec_dict = json.load(f)
oas = OpenAPI.parse_obj(spec_dict)

# %% ../nbs/oas_to_requests.ipynb 6
def get_request_body_from_schema(operation, oas):
    """Generates a default request body from the schema if `data` is not provided."""
    requestBody = operation.get("requestBody", {})
    if not requestBody: return None
    content = requestBody.get("content", {})
    schema_ref = content.get("application/json", {}).get("schema", {}).get("$ref")
    if schema_ref:
        schema_name = schema_ref.split("/")[-1]
        schema = oas.components.schemas.get(schema_name)
        if schema:
            return {"title": "Example Task", "completed": False}  # Example structure
    return None

# %% ../nbs/oas_to_requests.ipynb 8
def generate_request_by_operation_id(operation_id, parameters=None, data=None):
    return __generate_request_by_operation_id(oas, operation_id, parameters, data)
