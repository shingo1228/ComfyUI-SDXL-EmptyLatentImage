import torch
import json
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime


class SdxlEmptyLatentImage:
    """
    ComfyUI node for generating empty latent images with predefined resolutions.
    """
    
    _resolutions_cache = None
    _cache_timestamp = None
    
    # Basic configuration - can be overridden by environment variables
    CONFIG = {
        "max_resolution": int(os.environ.get("SDXL_MAX_RESOLUTION", "8192")),
        "min_resolution": int(os.environ.get("SDXL_MIN_RESOLUTION", "64")),
        "max_batch_size": int(os.environ.get("SDXL_MAX_BATCH_SIZE", "64")),
        "default_channels": int(os.environ.get("SDXL_DEFAULT_CHANNELS", "4")),
        "scale_factor": 8,
        "fallback_resolution": 1024,
        "track_usage": os.environ.get("SDXL_TRACK_USAGE", "true").lower() == "true"
    }
    
    def __init__(self):
        self.node_dir = os.path.dirname(os.path.realpath(__file__))
        self.usage_stats = self._load_usage_stats() if self.CONFIG["track_usage"] else {}
    
    def _load_usage_stats(self) -> Dict[str, Any]:
        """Load simple usage statistics."""
        stats_file = os.path.join(self.node_dir, "usage_stats.json")
        try:
            if os.path.exists(stats_file):
                with open(stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"favorites": [], "usage_count": {}, "recent": []}
    
    def _save_usage_stats(self) -> None:
        """Save usage statistics."""
        if not self.CONFIG["track_usage"]:
            return
        stats_file = os.path.join(self.node_dir, "usage_stats.json")
        try:
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception:
            pass
    
    def _record_usage(self, resolution_key: str) -> None:
        """Record resolution usage."""
        if not self.CONFIG["track_usage"]:
            return
        
        # Ensure keys exist
        if "usage_count" not in self.usage_stats:
            self.usage_stats["usage_count"] = {}
        if "recent" not in self.usage_stats:
            self.usage_stats["recent"] = []
        
        # Update usage count
        self.usage_stats["usage_count"][resolution_key] = self.usage_stats["usage_count"].get(resolution_key, 0) + 1
        
        # Update recent list (keep last 5)
        recent = self.usage_stats["recent"]
        if resolution_key in recent:
            recent.remove(resolution_key)
        recent.insert(0, resolution_key)
        self.usage_stats["recent"] = recent[:5]
        
        self._save_usage_stats()
    
    def _get_usage_marks(self, resolution_key: str) -> str:
        """Get usage marks for display."""
        if not self.CONFIG["track_usage"]:
            return ""
        
        marks = []
        if resolution_key in self.usage_stats.get("favorites", []):
            marks.append("★")
        if self.usage_stats.get("usage_count", {}).get(resolution_key, 0) >= 3:
            marks.append("🔥")
        if resolution_key in self.usage_stats.get("recent", []):
            marks.append("🕒")
        
        return " " + "".join(marks) if marks else ""
    
    def _load_resolutions(self) -> Dict[str, Dict[str, int]]:
        """Load resolutions from JSON files in the node directory."""
        current_time = os.path.getmtime(self.node_dir)
        
        # Simple cache check
        if (self._resolutions_cache is not None and 
            self._cache_timestamp is not None and 
            current_time <= self._cache_timestamp):
            return self._resolutions_cache
        
        resolutions = {}
        
        # Find all JSON files in the directory
        for filename in os.listdir(self.node_dir):
            if not filename.endswith(".json") or filename == "usage_stats.json":
                continue
            
            filepath = os.path.join(self.node_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    continue
                
                # Determine category from filename
                category = self._categorize_file(filename)
                
                for item in data:
                    if not isinstance(item, dict) or "width" not in item or "height" not in item:
                        continue
                    
                    try:
                        width = int(item["width"])
                        height = int(item["height"])
                        
                        if (width < self.CONFIG["min_resolution"] or height < self.CONFIG["min_resolution"] or
                            width > self.CONFIG["max_resolution"] or height > self.CONFIG["max_resolution"]):
                            continue
                        
                        aspect_ratio = width / height
                        key = f"[{category.upper()}] {width} x {height} ({aspect_ratio:.2f})"
                        
                        resolutions[key] = {
                            "width": width,
                            "height": height,
                            "category": category
                        }
                    except (ValueError, TypeError):
                        continue
                        
            except Exception:
                continue
        
        # Cache the results
        self._resolutions_cache = resolutions
        self._cache_timestamp = current_time
        return resolutions
    
    def _categorize_file(self, filename: str) -> str:
        """Determine category from filename."""
        filename_lower = filename.lower()
        if "sdxl" in filename_lower or "xl" in filename_lower:
            return "sdxl"
        elif "sd" in filename_lower or "1.5" in filename_lower or "15" in filename_lower:
            return "sd15"
        else:
            return "custom"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for ComfyUI."""
        instance = cls()
        resolutions = instance._load_resolutions()
        
        # Sort resolutions: Custom first, then SDXL, then SD15, sorted by aspect ratio within each category
        category_order = {"custom": 0, "sdxl": 1, "sd15": 2}
        sorted_keys = sorted(resolutions.keys(), key=lambda x: (
            category_order.get(resolutions[x]["category"], 2),
            resolutions[x]["width"] / resolutions[x]["height"]
        ))
        
        # Add usage marks
        if instance.CONFIG["track_usage"]:
            display_keys = [key + instance._get_usage_marks(key) for key in sorted_keys]
        else:
            display_keys = sorted_keys
        
        return {
            "required": {
                "resolution": (display_keys,),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": cls.CONFIG["max_batch_size"]}),
                "channels": (["4", "16"], {"default": str(cls.CONFIG["default_channels"])})
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"
    CATEGORY = "latent"
    
    def generate(self, resolution: str, batch_size: int = 1, channels: str = "4") -> Tuple[Dict[str, torch.Tensor]]:
        """Generate empty latent tensor."""
        try:
            # Remove usage marks from resolution key
            clean_resolution = resolution
            
            # Remove all possible usage marks (including multiple marks)
            marks_to_remove = ["★", "🔥", "🕒"]
            for mark in marks_to_remove:
                clean_resolution = clean_resolution.replace(" " + mark, "")
                clean_resolution = clean_resolution.replace(mark, "")  # Remove without space too
            
            # Remove any trailing whitespace and multiple marks combined
            clean_resolution = clean_resolution.strip()
            
            # Remove any remaining special characters at the end that aren't part of the resolution format
            while clean_resolution and not clean_resolution[-1].isalnum() and clean_resolution[-1] not in ')]}':
                clean_resolution = clean_resolution[:-1].strip()
            
            resolutions = self._load_resolutions()
            if clean_resolution not in resolutions:
                raise ValueError(f"Resolution '{clean_resolution}' not found")
            
            width = resolutions[clean_resolution]["width"]
            height = resolutions[clean_resolution]["height"]
            
            # Convert channels parameter to integer
            try:
                channels_int = int(channels)
                if channels_int not in [4, 16]:
                    raise ValueError(f"Unsupported channel count: {channels_int}")
            except ValueError:
                channels_int = self.CONFIG["default_channels"]
            
            # Record usage
            self._record_usage(clean_resolution)
            
            # Generate latent tensor
            latent = torch.zeros([
                batch_size,
                channels_int,
                height // self.CONFIG["scale_factor"],
                width // self.CONFIG["scale_factor"]
            ])
            
            return ({"samples": latent},)
            
        except Exception as e:
            print(f"Error generating latent: {e}")
            # Fallback to default resolution with specified channels
            fallback_size = self.CONFIG["fallback_resolution"]
            try:
                channels_int = int(channels)
                if channels_int not in [4, 16]:
                    channels_int = self.CONFIG["default_channels"]
            except ValueError:
                channels_int = self.CONFIG["default_channels"]
            
            fallback_latent = torch.zeros([
                batch_size, 
                channels_int, 
                fallback_size // self.CONFIG["scale_factor"], 
                fallback_size // self.CONFIG["scale_factor"]
            ])
            return ({"samples": fallback_latent},)


NODE_CLASS_MAPPINGS = {
    "SDXL Empty Latent Image": SdxlEmptyLatentImage,
}