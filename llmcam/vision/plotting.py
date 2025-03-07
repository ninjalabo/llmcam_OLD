"""Python module to generate plot from json data and download an plotted image via OpenAI API."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/vision/05_plotting.ipynb.

# %% auto 0
__all__ = ['plot_object']

# %% ../../nbs/vision/05_plotting.ipynb 3
from ..utils.file_manager import list_image_files, list_plot_files
from .yolo import detect_objects
from .gpt4v import ask_gpt4v_about_image_file

import os
import json
import matplotlib.pyplot as plt

# %% ../../nbs/vision/05_plotting.ipynb 16
def plot_object(
    images: list[str],  # List of images to be extracted
    object: str,  # Object to detect
    methods: list[str] = ["gpt", "yolo"],  # List of methods to use for extracting information. The available methods are "gpt" and "yolo"
):
    """
    Generate (only when requested) a bar plot displaying the number of instances of a specified object detected in a list of images, accepting only objects in singular form.
    Change the methods name to lowercase before passing to the function
    """
    # Determine local working directory and initiate path to save plot
    work_dir = os.getenv("LLMCAM_DATA", "../data")
    number = len(list_plot_files())
    path = os.path.join(work_dir, f"{number}_object_count_plot.jpg")

    # Determine which method to use
    yolo = any('yolo' in method.lower() for method in methods)
    gpt = any('gpt' in method.lower() for method in methods)

    # Initiate counts per image
    count_yolo = []
    count_gpt = []

    # Count objects in images
    if yolo:
        for image in images:
            image = work_dir + "/" + image.split("/")[-1]
            info = json.loads(detect_objects(image))
            count_yolo.append(info.get(object, 0))
    
    if gpt:
        for image in images:
            image = work_dir + "/" + image.split("/")[-1]
            info = json.loads(ask_gpt4v_about_image_file(image))
            count_gpt.append(info.get(object, 0))

    # Plot the number of objects detected per image
    if yolo and gpt:
        fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

        # YOLO plot
        axs[0].bar(images, count_yolo, color='skyblue')
        axs[0].set_title(f'YOLO: Number of {object} Detected')
        axs[0].set_ylabel(f'Number of {object}')
        axs[0].set_xlabel('Image')
        axs[0].set_xticks(range(len(images)))
        axs[0].set_xticklabels([f"Image {i+1}" for i in range(len(images))], rotation=45)
        axs[0].grid(axis='x', linestyle='--', alpha=0.7)

        # GPT-4 Vision plot
        axs[1].bar(images, count_gpt, color='lightcoral')
        axs[1].set_title(f'GPT: Number of {object} Detected')
        axs[0].set_xlabel('Image')
        axs[1].set_xticks(range(len(images)))
        axs[1].set_xticklabels([f"Image {i+1}" for i in range(len(images))], rotation=45)
        axs[1].grid(axis='x', linestyle='--', alpha=0.7)

        # Adjust layout
        plt.tight_layout()
        plt.savefig(path)
        plt.close()

    elif yolo or gpt:
        count = count_yolo if yolo else count_gpt
        plt.figure(figsize=(10, 6))
        plt.bar(images, count, color='skyblue')
        plt.title(f'Number of {object} Detected per Image')
        plt.xlabel('Image')
        plt.ylabel(f'Number of {object}')
        plt.xticks(range(len(images)), [f"Image {i+1}" for i in range(len(images))], rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Save plot
        plt.savefig(path)
        plt.close()

    return json.dumps({"path": path})
