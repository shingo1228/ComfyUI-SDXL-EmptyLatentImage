# ComfyUI-SDXL-EmptyLatentImage

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![日本語](https://img.shields.io/badge/lang-日本語-red.svg)](README.jp.md)

A simplified ComfyUI extension node that provides resolution selection with usage statistics for generating empty latent images.<br>
<img src="misc/ss_resolution_list.jpg" alt="Node image" style="width:300px; height:auto;">

## Features

### Core Functionality
- **Smart Resolution Selection**: Choose from pre-defined resolutions loaded from JSON files
- **Category-based Organization**: Automatic categorization with priority order: Custom → SDXL → SD15
- **Resolution Display**: Format `[Category] Width x Height (aspect_ratio)` with decimal aspect ratios

### Usage Statistics & Visual Feedback
- **Usage Tracking**: Automatic recording of resolution usage frequency
- **Visual Indicators**: Dynamic marks displayed after resolution labels:
  - ★ **Favorite** resolutions (manually registered)
  - 🔥 **Frequently used** resolutions (≥3 uses)
  - 🕒 **Recently used** resolutions (last 5 used)

### Simple Configuration
- **Environment Variables**: Override settings with `SDXL_*` environment variables
- **Basic JSON Config**: Simple `config.json` with essential settings only

## Resolution Display Order

Resolutions are displayed in the following priority order:
1. **Custom** resolutions (user-defined)
2. **SDXL** resolutions 
3. **SD15** resolutions

Within each category, resolutions are sorted by aspect ratio (portrait → square → landscape).

## JSON Format

Resolution files should follow this structure:
```json
[
    {
        "width": 1024, "height": 1024
    },
    {
        "width": 832, "height": 1152
    },
    {
        "width": 1152, "height": 832
    }
]
```

## Pre-included Resolution Sets
- **[sdxl_resolution_set.json](sdxl_resolution_set.json)**: Optimal SDXL training resolutions
- **[sd_resolution_set.json](sd_resolution_set.json)**: Standard SD1.5 resolution set
- **custom_resolution_set.json**: Your custom resolutions (create this file to add your own)

## Configuration

### Environment Variables
Override default settings:
- `SDXL_MAX_RESOLUTION`: Maximum allowed resolution (default: 8192)
- `SDXL_MIN_RESOLUTION`: Minimum allowed resolution (default: 64)
- `SDXL_MAX_BATCH_SIZE`: Maximum batch size (default: 64)
- `SDXL_TRACK_USAGE`: Enable/disable usage tracking (default: true)

### config.json (Optional)
Create or modify `config.json` for persistent settings:
```json
{
  "max_resolution": 8192,
  "min_resolution": 64,
  "max_batch_size": 64,
  "track_usage": true
}
```

## Managing Favorite Resolutions

### Adding Favorites
To mark resolutions as favorites, manually edit `usage_stats.json`:

```json
{
  "favorites": [
    "[CUSTOM] 1024 x 1024 (1.00)",
    "[SDXL] 832 x 1216 (0.68)"
  ],
  "usage_count": {},
  "recent": []
}
```

### Usage Statistics
The extension automatically tracks:
- **Usage Count**: Number of times each resolution is used
- **Recent History**: Last 5 used resolutions
- **Favorites**: Manually marked favorite resolutions

Example `usage_stats.json` after usage:
```json
{
  "favorites": [
    "[CUSTOM] 1024 x 1024 (1.00)"
  ],
  "usage_count": {
    "[SDXL] 1024 x 1024 (1.00)": 5,
    "[SDXL] 832 x 1216 (0.68)": 2
  },
  "recent": [
    "[SDXL] 832 x 1216 (0.68)",
    "[SDXL] 1024 x 1024 (1.00)"
  ]
}
```

## Install

1. Navigate to the `custom_nodes` folder where ComfyUI is installed
2. Clone the repository:
```bash
git clone https://github.com/shingo1228/ComfyUI-SDXL-EmptyLatentImage
```
3. (Optional) Add custom resolutions by creating `custom_resolution_set.json`:
```bash
cd ComfyUI-SDXL-EmptyLatentImage
# Create your custom resolution file
echo '[{"width": 1024, "height": 1024}, {"width": 512, "height": 768}]' > custom_resolution_set.json
```
4. (Optional) Customize settings in `config.json`
5. Restart ComfyUI to load the extension

## Architecture

This extension uses a simplified single-class design:
- **Single File**: All functionality in `sdxl_empty_latent.py`
- **Simple Caching**: Basic file modification time checking
- **Minimal Configuration**: Environment variables + optional JSON config
- **Essential Features Only**: Focus on core resolution selection and usage tracking

The simplified architecture makes the code easy to understand, modify, and maintain while providing all essential features for resolution management in ComfyUI workflows.