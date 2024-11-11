# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/oas_to_requests.ipynb.

# %% auto 0
__all__ = ['TRANSFERABLE_TYPES', 'extract_refs', 'transform_property', 'toolbox_schema', 'generate_request']

# %% ../nbs/oas_to_requests.ipynb 3
import requests
from pprint import pprint
import json
import yaml
import copy
import re

# %% ../nbs/oas_to_requests.ipynb 8
def extract_refs(
        oas: dict  # The OpenAPI schema
    ) -> dict:  # The extracted references (flattened)
    refs = copy.deepcopy(oas)
    refs_list = set()
    refs_locations = {}
    refs_dependencies = {}

    # Traverse the components section of the spec
    for section, items in refs["components"].items():
        for item in items:
            refs_list.add(f"components/{section}/{item}")
            refs_locations[f"components/{section}/{item}"] = []
            refs_dependencies[f"components/{section}/{item}"] = set()
    
    # Initialize the clean_refs set
    clean_refs = refs_list.copy()

    # Traverse the spec and extract the references
    def traverse_location(obj, path=""):
        for key, value in obj.items():
            if key == "$ref":
                # Determine the root of the reference and remove it from the clean_refs set
                ref_root = "/".join(path.split("/")[:3])
                clean_refs.discard(ref_root)

                # Extract the sub reference and add the current path to the list of locations
                sub_ref = value[2:]
                refs_locations[sub_ref].append(path)

                # Add the sub reference to the dependencies of the current reference
                refs_dependencies[ref_root].add(sub_ref)

            elif isinstance(value, dict):
                # Recursively traverse the object
                traverse_location(value, f"{path}/{key}")

    traverse_location(refs["components"], "components")

    # Attach the reference objects to the locations
    def attach_clean_refs():
        for ref in clean_refs:
            # Extract the reference object
            ref_obj = refs
            for part in ref.split("/"):
                ref_obj = ref_obj[part]

            # Extract the locations where the reference is used
            locations = refs_locations[ref]

            # Attach the reference object to the locations
            for location in locations:
                location_parts = location.split("/")

                obj = refs
                prev = None
                for part in location_parts:
                    prev = obj
                    obj = obj[part]

                prev[location_parts[-1]] = ref_obj

            # Remove the reference from the dependencies
            for dependency in refs_dependencies:
                refs_dependencies[dependency].discard(ref)

    # Check if there are any clean references
    def check_clean_refs():
        clean_refs = set()
        for ref, dependencies in refs_dependencies.items():
            if len(dependencies) == 0:
                clean_refs.add(ref)
        return clean_refs
    
    # Iterate until all references are attached or no progress is made
    prev_nof_clean = None
    while len(clean_refs) < len(refs_list) and prev_nof_clean != len(clean_refs):
        prev_nof_clean = len(clean_refs)
        attach_clean_refs()
        clean_refs = check_clean_refs()

    # Flatten the references
    flatten_refs = {}
    for section, items in refs["components"].items():
        for item in items:
            flatten_refs[f"#/components/{section}/{item}"] = refs["components"][section][item]

    return flatten_refs

# %% ../nbs/oas_to_requests.ipynb 14
# Directly transferable properties from OAS to GPT-compatible schema
TRANSFERABLE_TYPES = [
    "type", "description", "default", "enum", "pattern", "additionalProperties",
    "minLength", "maxLength", "minItems", "maxItems"
]

# Function to transform OAS schema to GPT-compatible schema
def transform_property(
        prop: dict,  # The property to transform
        flatten_refs: dict = {}  # The flattened references
    ) -> tuple[dict, bool]:  # The transformed property and whether it is a required property

    # If the property is a schema, flatten it
    if "schema" in prop:
        prop = copy.deepcopy(prop)
        prop.update(prop["schema"])
        prop.pop("schema")

    # Extract the required field
    required = prop.get("required", False)
    
    # If the property is a reference, return it as is
    if "$ref" in prop:
        if prop["$ref"] in flatten_refs:
            ref_prop, _ = transform_property(flatten_refs[prop["$ref"]], flatten_refs)
            return ref_prop, required
        else:
            # If the reference is not found, return the reference as is
            return prop, required 
    
    # If the property is an object, transform it
    new_prop = {}
    additionals = {}

    # If required is a list, it is directly transferable to GPT-compatible schema
    if isinstance(required, list): 
        new_prop["required"] = required
        required = True

    for key, value in prop.items():
        if key in TRANSFERABLE_TYPES:
            new_prop[key] = value
        elif key == "items":
            # Handle array items recursively
            item_prop, _ = transform_property(value, flatten_refs)
            new_prop[key] = item_prop
        elif key == "properties":
            # Handle nested properties recursively
            new_prop[key] = {}
            new_prop["required"] = [] if "required" not in new_prop else new_prop["required"]
            for sub_key, sub_value in value.items():
                sub_prop, sub_required = transform_property(sub_value, flatten_refs)
                new_prop[key][sub_key] = sub_prop
                if sub_required:
                    new_prop["required"].append(sub_key)
        elif key == "required":
            # Skip required field since it is handled in the properties section
            continue
        else:
            # Collect unrecognized fields in additionals dictionary
            additionals[key] = value

    # Add the additionals dictionary if it is not empty
    if len(additionals) > 0:
        additional_info = "; ".join([f"{k.capitalize()}: {v}" for k, v in additionals.items()])
        if "description" in new_prop:
            new_prop["description"] += f" ({additional_info})"
        else:
            new_prop["description"] = f"({additional_info})"

    # Remove None values and return the transformed property
    return {k: v for k, v in new_prop.items() if v is not None}, required


# %% ../nbs/oas_to_requests.ipynb 20
def toolbox_schema(
        base_url: str,  # The base URL of the API
        oas: dict,  # The OpenAPI schema
    ) -> dict:  # The toolbox schema
    """Form the toolbox schema from the OpenAPI schema."""
    
    # Extract the references
    flatten_refs = extract_refs(oas)
    
    # Initialize the toolbox
    toolbox = []

    # Traverse the paths section of the spec
    for path, methods in oas["paths"].items():
        for method, info in methods.items():
            # Extract the function name
            name = info["operationId"] if "operationId" in info else \
                f"{method}{path.replace('/', '_').replace('{', 'by').replace('}', '').replace('-', '_')}"
            name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

            # Extract the function description
            description = info["description"] if "description" in info else info.get("summary", "")

            # Extract the function parameters
            parameters = {
                "type": "object",

                # Initialize with the constant properties - path and method of endpoint
                "properties": {
                    "url": {"type": "string", "enum": [base_url + path], "default": base_url + path},
                    "method": {"type": "string", "enum": [method], "default": method},
                },

                # Initialize the required properties
                "required": ["url", "method"]
            }

            # Extract endpoint parameters
            if "parameters" in info:
                for param in info["parameters"]:
                    # Extract the parameter location (query, path, header, cookie)
                    location = param.get("in", "query")

                    # Initialize the parameter object based on location
                    if location not in parameters["properties"]:
                        parameters["properties"][location] = {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }

                    # Extract the parameter schema
                    param_obj, required = transform_property(param, flatten_refs)

                    # Add the parameter to the toolbox
                    parameters["properties"][location]["properties"][param["name"]] = param_obj
                    if required or location == "path":
                        parameters["properties"][location]["required"].append(param["name"])
                        parameters["required"].append(location)
                    
            # Extract the function body
            body = {}
            if "requestBody" in info and "content" in info["requestBody"] \
                    and "application/json" in info["requestBody"]["content"] \
                    and "schema" in info["requestBody"]["content"]["application/json"]:
                body = info["requestBody"]["content"]["application/json"]
                body, _ = transform_property(body, flatten_refs)
                parameters["properties"]["body"] = body
                parameters["required"].append("body")

            # Remove duplicate required properties
            parameters["required"] = list(set(parameters["required"]))
                
            # Conclude the function information
            function = {
                "name": name,
                "description": description,
                "parameters": parameters
            }

            # Add the function to the toolbox
            toolbox.append(
                {
                    "type": "function",
                    "function": function
                }
            )
        
    return toolbox

# %% ../nbs/oas_to_requests.ipynb 25
def generate_request(
    function_name: str,  # The name of the function
    tools: list = [],  # The toolbox schema
    url: str = None,  # The URL of the request
    method: str = None,  # The method of the request
    path: dict = {},  # The path parameters of the request
    query: dict = {},  # The query parameters of the request
    body: dict = {},  # The body of the request
    **kwargs  # Additional parameters
) -> dict:  # The response of the request
    """Generate a request from the function name and parameters."""
    # Extract the URL and method from the toolbox if not provided
    if url is None or method is None:
        for tool in tools:
            if tool["function"]["name"] == function_name:
                url = tool["function"]["parameters"]["properties"]["url"]["default"]
                method = tool["function"]["parameters"]["properties"]["method"]["default"]
                break

    # Prepare the request
    headers = {
        "Content-Type": "application/json"
    }

    # Execute the request
    response = requests.request(
        method,
        url.format(**path, **kwargs),
        headers=headers,
        params={**query, **kwargs},
        json=body if len(body) > 0 else None
    )

    # Return the response (either as JSON or text)
    try:
        return response.json()
    except:
        return {"message": response.text}
