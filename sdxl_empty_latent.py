import torch
import json
import os

MAX_RESOLUTION=8192

def extract_resolutions_with_key(file_path):
    """指定したJSONファイルからwidthとheightのペアを取得し、
    "width x height" 形式のキー項目とともに辞書を返す。
    """
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    
    resolutions_dict = {}
    for item in json_data:
        width = item.get('width')
        height = item.get('height')
        if width and height:
            key = f"{width} x {height}"
            resolutions_dict[key] = {'width': width, 'height': height}
    
    return resolutions_dict

class SdxlEmptyLatentImage:
    def __init__(self, device="cpu"):
        self.device = device

        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_file_name = os.path.join(current_dir, "sdxl_resolution_set.json")

        self.resolutions  = extract_resolutions_with_key(json_file_name)
        for key, item in self.resolutions.items():
            print(f"key:{key} w:{item['width']} h:{item['height']}")

    @classmethod
    def INPUT_TYPES(s):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_file_name = os.path.join(current_dir, "sdxl_resolution_set.json")

        resolutions  = extract_resolutions_with_key(json_file_name)
        res_list = []
        for key in resolutions:
            res_list.append(key)
        print(res_list)

        return {"required": { "resolution": (res_list,),
                              "batch_size": ("INT", {"default": 1, "min": 1, "max": 64})
                              }}

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"

    CATEGORY = "latent"

    def generate(self, resolution, batch_size=1):
        print(f"res_key:{resolution}")
        print(f"item:{self.resolutions[resolution]}")

        latent = torch.zeros([batch_size, 4, self.resolutions[resolution]['height'] // 8, self.resolutions[resolution]['width'] // 8])
        return ({"samples":latent}, )

NODE_CLASS_MAPPINGS = {
    "SDXL Empty Latent Image": SdxlEmptyLatentImage,
}
