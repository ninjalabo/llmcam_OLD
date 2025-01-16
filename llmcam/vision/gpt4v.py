"""Python module for processing image by asking GPT via OpenAI API"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/vision/02_gpt4v.ipynb.

# %% auto 0
__all__ = ['question', 'CITY_INFO', 'SATELLITE_INFO', 'encode_image', 'info', 'ask_gpt4v_about_image_file']

# %% ../../nbs/vision/02_gpt4v.ipynb 3
from IPython.display import Image
import base64
import glob
import json
import openai
import requests

# %% ../../nbs/vision/02_gpt4v.ipynb 7
def encode_image(fname: str):
    """Encode an image file as base64 string"""
    with open(fname, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# %% ../../nbs/vision/02_gpt4v.ipynb 12
question = """
    Describe this image quantitatively as many as possible in json format. All the value should numbers.
    
    ##### EXAMPLE OUTPUT FORMAT
    {
        'timestamp': '2024-10-06T19:04:14',
        'location': 'Kauppatori',
        'dimensions': '1280 x 720',
        'building': 10,
        'buildings_height_range': '3-5 stories',
        'car': 5,
        'truck': 2,
        'boat': 4,
        'available_parking_space': 3,
        'street_lights': 20,
        'person': 10,
        'time_of_day': 'evening',
        'artificial_lighting': 'prominent',
        'visibility_clear': True,
        'sky_visible': True,
        'sky_light_conditions': 'dusk',
        'waterbodies_visible': True,
        'waterbodies_type': 'harbor'
    }
    """

# %% ../../nbs/vision/02_gpt4v.ipynb 15
def info(response):
    txt = json.loads(response.json())['choices'][0]['message']['content']
    data = json.loads(txt.replace('```json\n', "").replace('\n```', ""))
    return data

# %% ../../nbs/vision/02_gpt4v.ipynb 19
CITY_INFO = { "properties": {
    "timestamp": {
        "type": "string",
        "format": "date-time",
        "description": "The timestamp of when the data was collected or observed."
    },
    "location": {
        "type": "string",
        "description": "The name or description of the location being observed."
    },
    "dimensions": {
        "type": "string",
        "description": "The resolution or dimensions of the captured scene, typically in width x height format."
    },
    "building": {
        "type": "integer",
        "description": "The number of buildings visible in the scene."
    },
    "buildings_height_range": {
        "type": "string",
        "description": "The range of building heights visible, described in stories."
    },
    "car": {
        "type": "integer",
        "description": "The number of cars visible in the scene."
    },
    "truck": {
        "type": "integer",
        "description": "The number of trucks visible in the scene."
    },
    "boat": {
        "type": "integer",
        "description": "The number of boats visible in the scene."
    },
    "available_parking_space": {
        "type": "integer",
        "description": "The number of available parking spaces visible."
    },
    "street_lights": {
        "type": "integer",
        "description": "The number of street lights visible in the scene."
    },
    "person": {
        "type": "integer",
        "description": "The number of people visible in the scene."
    },
    "time_of_day": {
        "type": "string",
        "description": "The general time of day (e.g., morning, afternoon, evening, night)."
    },
    "artificial_lighting": {
        "type": "string",
        "description": "The prominence of artificial lighting in the scene."
    },
    "visibility_clear": {
        "type": "boolean",
        "description": "Whether the visibility in the scene is clear."
    },
    "sky_visible": {
        "type": "boolean",
        "description": "Whether the sky is visible in the scene."
    },
    "sky_light_conditions": {
        "type": "string",
        "description": "The lighting conditions of the sky (e.g., clear, overcast, dusk)."
    },
    "waterbodies_visible": {
        "type": "boolean",
        "description": "Whether water bodies are visible in the scene."
    },
    "waterbodies_type": {
        "type": "string",
        "description": "The type of water bodies visible (e.g., river, lake, harbor)."
    }
},
"required": ["timestamp", "location", "dimensions"]
}

# %% ../../nbs/vision/02_gpt4v.ipynb 22
SATELLITE_INFO = {
    "properties": {
      "timestamp": {
        "type": "string",
        "format": "date-time",
        "description": "The exact timestamp when the satellite image was captured."
      },
      "location": {
        "type": "string",
        "description": "The primary location or region of the image (e.g., Indian Ocean)."
      },
      "latitude": {
        "type": "number",
        "description": "The latitude of the image's focus area in decimal degrees."
      },
      "longitude": {
        "type": "number",
        "description": "The longitude of the image's focus area in decimal degrees."
      },
      "image_dimensions": {
        "type": "string",
        "description": "The pixel dimensions of the image, typically in width x height format."
      },
      "satellite_name": {
        "type": "string",
        "description": "The name of the satellite that captured the image (e.g., International Space Station)."
      },
      "sensor_type": {
        "type": "string",
        "description": "The type of sensor used for capturing the image (e.g., Optical, Infrared, Radar)."
      },
      "cloud_cover_percentage": {
        "type": "number",
        "description": "The percentage of the image obscured by clouds."
      },
      "land_cover_types": {
        "type": "array",
        "description": "List of land cover types visible in the image (e.g., ocean, forest, urban).",
        "items": {
          "type": "string"
        }
      },
      "waterbodies_detected": {
        "type": "boolean",
        "description": "Indicates whether water bodies are detected in the image."
      },
      "waterbodies_type": {
        "type": "string",
        "description": "The type of water bodies detected (e.g., Ocean, River, Lake).",
      },
      "urban_areas_detected": {
        "type": "boolean",
        "description": "Indicates whether urban areas are visible in the image."
      },
      "lightning_detected": {
        "type": "boolean",
        "description": "Indicates whether lightning strikes are detected in the image."
      },
      "vegetation_index": {
        "type": "number",
        "description": "Normalized vegetation index (e.g., NDVI) if vegetation is present.",
      },
      "thermal_anomalies_detected": {
        "type": "boolean",
        "description": "Indicates whether thermal anomalies are detected in the image."
      },
      "nighttime_imaging": {
        "type": "boolean",
        "description": "Indicates whether the image was captured at night."
      },
      "mins_to_sunset": {
        "type": "number",
        "format": "integer",
        "description": "The expected minutes until sunset if the image was captured near sunset."
      },
      "mins_to_sunrise": {
        "type": "number",
        "format": "integer",
        "description": "The expected minutes until sunrise if the image was captured near sunrise."
      },
      "satellite_speed_kms": {
        "type": "string",
        "description": "The speed of the satellite in km/s at the time of capture."
      },
      "satellite_altitude_km": {
        "type": "string",
        "description": "The altitude of the satellite in kilometers above the Earth's surface."
      },
    },
    "required": [
      "location",
      "image_dimensions",
      "satellite_name",
      "sensor_type",
      "cloud_cover_percentage",
      "waterbodies_detected",
      "urban_areas_detected",
      "lightning_detected",
      "thermal_anomalies_detected",
      "nighttime_imaging"
    ]
}

# %% ../../nbs/vision/02_gpt4v.ipynb 24
def ask_gpt4v_about_image_file(
        path: str,  # Path to the image file
        image_type: str = "city", # Type of image: "city" or "satellite", default is "city"
    ) -> str:  # JSON string with quantitative information
    """Tell all about quantitative information from a given image file"""
    info_format = CITY_INFO if image_type == "city" else SATELLITE_INFO
    response = openai.chat.completions.create(
      model="gpt-4o",
      messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image quantitatively as many as possible in json format."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encode_image(path)}", "detail":"high",},
                },
            ],
        }],
      functions=[
          {
              "name": "image_quantitative_analysis",
                "description": "Extract quantitative information from an image.",
                "parameters": {
                    "type": "object",
                    **info_format,
                    "additionalProperties": True
                }
          }
      ],
      function_call={"name": "image_quantitative_analysis"},
      max_tokens=300,
    )
    parsed_data = response.choices[0].message.function_call.arguments
    json_data = json.dumps(json.loads(parsed_data), indent=4)
    
    return json_data
