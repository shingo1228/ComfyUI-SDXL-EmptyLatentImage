import torch
import json
import os

MAX_RESOLUTION = 8192
DEBUG = False


def extract_resolutions_with_key(file_path):
    with open(file_path, "r") as file:
        json_data = json.load(file)

    resolutions_dict = {}
    for item in json_data:
        width = item["width"]
        height = item["height"]
        aspect_ratio = "{:.2f}".format(round(width / height, 2))
        key = f"{width} x {height} ({aspect_ratio})"
        resolutions_dict[key] = {"width": width, "height": height}

    return resolutions_dict


class SdxlEmptyLatentImage:
    def __init__(self, device="cpu"):
        self.device = device

        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_file_name = os.path.join(current_dir, "sdxl_resolution_set.json")
        self.resolutions = extract_resolutions_with_key(json_file_name)

        if DEBUG:
            for key, item in self.resolutions.items():
                print(f"key:{key} w:{item['width']} h:{item['height']}")

    @classmethod
    def INPUT_TYPES(s):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_file_name = os.path.join(current_dir, "sdxl_resolution_set.json")

        resolutions = extract_resolutions_with_key(json_file_name)
        res_list = []
        for key in resolutions:
            res_list.append(key)

        if DEBUG:
            print(res_list)

        return {
            "required": {
                "resolution": (res_list,),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"

    CATEGORY = "latent"

    def generate(self, resolution, batch_size=1):
        if DEBUG:
            print(f"res_key:{resolution}")
            print(f"item:{self.resolutions[resolution]}")

        latent = torch.zeros(
            [
                batch_size,
                4,
                self.resolutions[resolution]["height"] // 8,
                self.resolutions[resolution]["width"] // 8,
            ]
        )
        return ({"samples": latent},)


NODE_CLASS_MAPPINGS = {
    "SDXL Empty Latent Image": SdxlEmptyLatentImage,
}
