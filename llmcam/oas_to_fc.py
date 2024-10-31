"""This notebook is to validate OAS -> FC (Function-Calling) conversion and implement python module for that."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../nbs/04_oas_to_fc.ipynb.

# %% auto 0
__all__ = []

# %% ../../../nbs/04_oas_to_fc.ipynb 3
from fastapi import FastAPI
from typing import Optional
import uvicorn
import threading
import httpx
import json
import openai
