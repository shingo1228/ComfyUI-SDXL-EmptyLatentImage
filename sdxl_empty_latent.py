import torch
import json
import os

MAX_RESOLUTION = 8192
DEBUG = False


def get_all_json_files(directory):
    return [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if file.endswith(".json") and os.path.isfile(os.path.join(directory, file))
    ]


def load_resolutions_from_directory(directory):
    json_files = get_all_json_files(directory)

    if DEBUG:
        for json_file in json_files:
            print(f"json_file:{json_file}")

    resolutions_dict = {}
    for json_file in json_files:
        with open(json_file, "r") as file:
            json_data = json.load(file)

        for item in json_data:
            width = item["width"]
            height = item["height"]
            aspect_ratio = "{:.2f}".format(round(width / height, 2))
            key = f"{width} x {height} ({aspect_ratio})"
            resolutions_dict[key] = {"width": width, "height": height}

    return resolutions_dict


class SdxlEmptyLatentImage:
    resolution_dictionaly = None

    def __init__(self, device="cpu"):
        self.device = device

        if self.resolution_dictionaly is None:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            self.resolution_dictionaly = load_resolutions_from_directory(current_dir)

        if DEBUG:
            for key, item in self.resolution_dictionaly.items():
                print(f"key:{key} w:{item['width']} h:{item['height']}")

    @classmethod
    def INPUT_TYPES(s):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        if s.resolution_dictionaly is None:
            s.resolution_dictionaly = load_resolutions_from_directory(current_dir)

        res_list = []
        for key in s.resolution_dictionaly:
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
            print(f"item:{self.resolution_dictionaly[resolution]}")

        latent = torch.zeros(
            [
                batch_size,
                4,
                self.resolution_dictionaly[resolution]["height"] // 8,
                self.resolution_dictionaly[resolution]["width"] // 8,
            ]
        )
        return ({"samples": latent},)


NODE_CLASS_MAPPINGS = {
    "SDXL Empty Latent Image": SdxlEmptyLatentImage,
}
