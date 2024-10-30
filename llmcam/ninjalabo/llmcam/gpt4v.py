"""ask gpt4v via openai api"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../nbs/02_gpt4v.ipynb.

# %% auto 0
__all__ = ['question', 'encode_image', 'info', 'gpt4v']

# %% ../../../nbs/02_gpt4v.ipynb 3
import json
import base64
import requests
from openai import OpenAI

# %% ../../../nbs/02_gpt4v.ipynb 7
def encode_image(fname: str):
    "encode an image file as base64"
    with open(fname, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# %% ../../../nbs/02_gpt4v.ipynb 13
def info(response):
    txt = json.loads(response.json())['choices'][0]['message']['content']
    data = json.loads(txt.replace('```json\n', "").replace('\n```', ""))
    return data

# %% ../../../nbs/02_gpt4v.ipynb 14
question = """
    Describe this image quantitatively as many as possible in json format.
    
    Here's the example:
    {'timestamp': '2024-10-06T19:04:14',
     'location': 'Kauppatori',
     'dimensions': {'width': 1280, 'height': 720},
     'buildings': {'number_of_buildings': 10,
      'building_height_range': '3-5 stories'},
     'vehicles': {'number_of_vehicles': 5, 'types': ['cars', 'trucks'], number_of_available_parking_space: 3},
     'waterbodies': {'visible': True, 'type': 'harbor', 'number_of_boats': 4},
     'street_lights': {'number_of_street_lights': 20},
     'people': {'approximate_number': 10},
     'lighting': {'time_of_day': 'evening', 'artificial_lighting': 'prominent'},
     'visibility': {'clear': True},
     'sky': {'visible': True, 'light_conditions': 'dusk'}}
    """

# %% ../../../nbs/02_gpt4v.ipynb 17
class gpt4v:
    def __init__(self):
        self.api = OpenAI()

    def ask_text(self, question):
        completion = self.api.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": question}
            ]
        )
        return completion.choices[0].message.content

    def ask(self, fname, question=question):
        response = self.api.chat.completions.create(
          model="gpt-4o",
          messages=[
            {
              "role": "user",
              "content": [
                {
                  "type": "text",
                  "text": question,
                },
                {
                  "type": "image_url",
                  "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image(fname)}",
                    "detail": "high",
                  },
                },
                # {
                #   "type": "image_url",
                #   "image_url": {
                #     "url": f"data:image/jpeg;base64,{encode_image(files[1])}"
                #   },
                # },
              ],
            }
          ],
          max_tokens=300,
        )
        return info(response)
