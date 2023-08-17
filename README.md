# ComfyUI-SDXL-EmptyLatentImage
[Japanese README](README.jp.md)

An extension node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that allows you to select a resolution from the pre-defined json files and output a Latent Image.
![](misc/ss_resolution_list.png)
## Features
- You can retrieve a list of resolutions from a json file saved in the format below and select from the node's dropdown list.(The aspect ratio displayed in the dropdown is calculated as `width / height`.)
```
[
    {
        "width": 704, "height": 1408
    },
    {
        "width": 704, "height": 1344
    }
]
```
- The [sdxl_resolution_set.json](sdxl_resolution_set.json) file already contains a set of resolutions considered optimal for training in SDXL.
- Following the above, you can load a *.json file during node initialization, allowing you to save custom resolution settings in a separate file. (As a sample, we have prepared a resolution set for SD1.5 in [sd_resolution_set.json](sd_resolution_set.json).)
## Install
1. Navigate to the `cusom_nodes` folder where ComfyUI is installed.
2. Use the `git clone` command to clone the [ComfyUI-SDXL-EmptyLatentImage](https://github.com/shingo1228/ComfyUI-SDXL-EmptyLatentImage) repository.<br>
`git clone https://github.com/shingo1228/ComfyUI-SDXL-EmptyLatentImage`
