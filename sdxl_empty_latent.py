import torch
import json
import os
import logging
from typing import Dict, List, Any, Tuple, Optional

# Import interfaces for better testability
try:
    from .interfaces import ResolutionManagerInterface, CacheInterface, LatentGeneratorInterface
except ImportError:
    # Fallback for when interfaces module is not available
    from abc import ABC, abstractmethod
    
    class ResolutionManagerInterface(ABC):
        @abstractmethod
        def get_sorted_resolution_list(self) -> List[str]: pass
        @abstractmethod  
        def get_resolution_data(self, resolution_key: str) -> Optional[Dict[str, Any]]: pass
    
    class CacheInterface(ABC):
        @abstractmethod
        def is_valid(self, key: str) -> bool: pass
    
    class LatentGeneratorInterface(ABC):
        @abstractmethod
        def generate_latent(self, width: int, height: int, batch_size: int) -> Dict[str, Any]: pass

# Configuration management
class Config:
    """Configuration manager for SDXL Empty Latent Image node."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from config.json and environment variables."""
        # Default configuration
        self._config = {
            "resolution_limits": {
                "max_resolution": 8192,
                "min_resolution": 64
            },
            "batch_settings": {
                "default_batch_size": 1,
                "min_batch_size": 1,
                "max_batch_size": 64
            },
            "latent_settings": {
                "channels": 4,
                "scale_factor": 8,
                "fallback_resolution": 1024
            },
            "display_settings": {
                "aspect_ratio_precision": 2,
                "sort_by_size": False,
                "group_by_aspect_ratio": False
            },
            "performance": {
                "enable_cache": True,
                "cache_validation": True
            },
            "logging": {
                "debug": False,
                "log_level": "WARNING",
                "log_file_operations": False,
                "log_resolution_loading": False
            }
        }
        
        # Load from config.json if exists
        try:
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    self._merge_config(self._config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
        
        # Override with environment variables
        self._load_env_overrides()
        
        # Setup logging
        self._setup_logging()
    
    def _merge_config(self, base: dict, override: dict) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mappings = {
            "SDXL_DEBUG": ("logging", "debug", lambda x: x.lower() in ["true", "1", "yes"]),
            "SDXL_LOG_LEVEL": ("logging", "log_level", str),
            "SDXL_MAX_RESOLUTION": ("resolution_limits", "max_resolution", int),
            "SDXL_MAX_BATCH_SIZE": ("batch_settings", "max_batch_size", int),
            "SDXL_ENABLE_CACHE": ("performance", "enable_cache", lambda x: x.lower() in ["true", "1", "yes"]),
        }
        
        for env_var, (section, key, converter) in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                try:
                    self._config[section][key] = converter(env_value)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid environment variable {env_var}={env_value}: {e}")
    
    def _setup_logging(self) -> None:
        """Setup logging based on configuration."""
        log_config = self._config["logging"]
        level = getattr(logging, log_config["log_level"].upper(), logging.WARNING)
        
        # Configure logger for this module
        logger = logging.getLogger(__name__)
        logger.setLevel(level)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add console handler if debug is enabled
        if log_config["debug"]:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def get(self, section: str, key: str, default=None):
        """Get configuration value."""
        return self._config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> dict:
        """Get entire configuration section."""
        return self._config.get(section, {})

# Global configuration instance
config = Config()
logger = logging.getLogger(__name__)


def get_all_json_files(directory: str) -> List[str]:
    """
    Get all JSON files from directory with optimized file checks.
    
    Args:
        directory: Path to directory to scan for JSON files
        
    Returns:
        List of absolute paths to JSON files found in the directory
        
    Raises:
        None - OSErrors are handled gracefully with warnings
    """
    json_files = []
    try:
        for file in os.listdir(directory):
            if not file.endswith(".json"):
                continue
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                json_files.append(file_path)
    except OSError as e:
        if config.get("logging", "log_file_operations"):
            logger.warning(f"Error reading directory {directory}: {e}")
        else:
            print(f"Warning: Error reading directory {directory}: {e}")
    
    return json_files


def load_resolutions_from_directory(directory: str) -> Dict[str, Dict[str, int]]:
    """
    Load resolution settings from all JSON files in the specified directory.
    
    Args:
        directory: Path to directory containing JSON resolution files
        
    Returns:
        Dictionary mapping resolution strings to width/height dictionaries
        Format: {"1024 x 1024 (1.00)": {"width": 1024, "height": 1024}}
        
    Raises:
        None - Errors are handled gracefully with warnings
    """
    json_files = get_all_json_files(directory)

    if config.get("logging", "log_resolution_loading"):
        logger.info(f"Found {len(json_files)} JSON files: {json_files}")

    resolutions_dict = {}
    max_resolution = config.get("resolution_limits", "max_resolution")
    min_resolution = config.get("resolution_limits", "min_resolution")
    aspect_precision = config.get("display_settings", "aspect_ratio_precision")
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                json_data = json.load(file)
        except FileNotFoundError:
            logger.warning(f"JSON file not found: {json_file}")
            continue
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON format in {json_file}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Error reading {json_file}: {e}")
            continue

        if not isinstance(json_data, list):
            logger.warning(f"Expected list in {json_file}, got {type(json_data)}")
            continue

        for item in json_data:
            try:
                if not isinstance(item, dict):
                    logger.warning(f"Expected dict in {json_file}, got {type(item)}")
                    continue
                
                if "width" not in item or "height" not in item:
                    logger.warning(f"Missing width or height in {json_file}")
                    continue
                
                width = int(item["width"])
                height = int(item["height"])
                
                if width <= 0 or height <= 0:
                    logger.warning(f"Invalid dimensions {width}x{height} in {json_file}")
                    continue
                
                if width < min_resolution or height < min_resolution:
                    logger.warning(f"Resolution {width}x{height} below minimum {min_resolution} in {json_file}")
                    continue
                
                if width > max_resolution or height > max_resolution:
                    logger.warning(f"Resolution {width}x{height} exceeds maximum {max_resolution} in {json_file}")
                    continue
                
                # Format aspect ratio as decimal number
                aspect_ratio_display = format_aspect_ratio_display(width, height)
                
                # Add category metadata
                category = categorize_resolution_source(json_file)
                
                # Create enhanced resolution key with category and aspect ratio
                display_config = config.get_section("display_settings")
                
                if display_config.get("enable_category_filter") and display_config.get("show_category_prefix"):
                    key = f"[{category.upper()}] {width} x {height} ({aspect_ratio_display})"
                else:
                    key = f"{width} x {height} ({aspect_ratio_display})"
                
                resolutions_dict[key] = {
                    "width": width, 
                    "height": height,
                    "category": category,
                    "aspect_ratio": width / height,  # Numerical ratio for sorting
                    "pixel_count": width * height,
                    "source_file": os.path.basename(json_file)
                }
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid width/height values in {json_file}: {e}")
                continue

    return resolutions_dict


def categorize_resolution_source(json_file: str) -> str:
    """
    Determine the category of a resolution source file.
    
    Args:
        json_file: Path to the JSON file
        
    Returns:
        Category string (sdxl, sd15, custom)
    """
    filename = os.path.basename(json_file).lower()
    display_config = config.get_section("display_settings")
    category_detection = display_config.get("category_detection", {})
    
    # Check SDXL patterns
    for pattern in category_detection.get("sdxl_patterns", []):
        if pattern in filename:
            return "sdxl"
    
    # Check SD1.5 patterns
    for pattern in category_detection.get("sd15_patterns", []):
        if pattern in filename:
            return "sd15"
    
    # Check custom patterns
    for pattern in category_detection.get("custom_patterns", []):
        if pattern in filename:
            return "custom"
    
    return "custom"


def calculate_aspect_ratio_gcd(width: int, height: int) -> Tuple[int, int]:
    """
    Calculate aspect ratio as simplified integer ratio using GCD.
    
    Args:
        width: Resolution width
        height: Resolution height
        
    Returns:
        Tuple of (width_ratio, height_ratio) as simplified integers
    """
    import math
    
    # Find the greatest common divisor
    gcd = math.gcd(width, height)
    
    # Simplify the ratio
    width_ratio = width // gcd
    height_ratio = height // gcd
    
    return width_ratio, height_ratio


def format_aspect_ratio_display(width: int, height: int) -> str:
    """
    Format aspect ratio for display as decimal number.
    
    Args:
        width: Resolution width  
        height: Resolution height
        
    Returns:
        Formatted string like "1.33" or "1.78"
    """
    aspect_precision = config.get("display_settings", "aspect_ratio_precision", 2)
    return f"{width / height:.{aspect_precision}f}"


class CacheManager(CacheInterface):
    """Manages file caching and validation for resolution files."""
    
    def __init__(self):
        self._last_modified_times: Optional[Dict[str, float]] = None
    
    def get_modification_times(self, directory: str) -> Dict[str, float]:
        """
        Get modification times of all JSON files for cache validation.
        
        Args:
            directory: Directory containing JSON files
            
        Returns:
            Dictionary mapping file paths to modification times
        """
        modification_times: Dict[str, float] = {}
        json_files = get_all_json_files(directory)
        
        for json_file in json_files:
            try:
                modification_times[json_file] = os.path.getmtime(json_file)
            except OSError:
                modification_times[json_file] = 0
                
        return modification_times
    
    def is_valid(self, key: str) -> bool:
        """Check if cache entry is valid (implementing CacheInterface)."""
        return self.is_cache_valid(key)
    
    def update(self, key: str, data: Any) -> None:
        """Update cache entry (implementing CacheInterface)."""
        self.update_cache_timestamp(key)
    
    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry (implementing CacheInterface)."""
        if key is None:
            self.invalidate_cache()
    
    def is_cache_valid(self, directory: str) -> bool:
        """
        Check if cached data is still valid by comparing file modification times.
        
        Args:
            directory: Directory to check
            
        Returns:
            True if cache is valid, False if needs refresh
        """
        if self._last_modified_times is None:
            return False
            
        current_modification_times = self.get_modification_times(directory)
        return current_modification_times == self._last_modified_times
    
    def update_cache_timestamp(self, directory: str) -> None:
        """
        Update the cache timestamp to current file modification times.
        
        Args:
            directory: Directory to update timestamp for
        """
        self._last_modified_times = self.get_modification_times(directory)
    
    def invalidate_cache(self) -> None:
        """Invalidate the current cache."""
        self._last_modified_times = None


def classify_aspect_ratio(width: int, height: int) -> str:
    """
    Classify resolution by aspect ratio group.
    
    Args:
        width: Resolution width
        height: Resolution height
        
    Returns:
        Aspect ratio group name (square, portrait, landscape)
    """
    aspect_ratio = width / height
    display_config = config.get_section("display_settings")
    aspect_groups = display_config.get("aspect_ratio_groups", {})
    
    for group_name, group_config in aspect_groups.items():
        if group_config["min"] <= aspect_ratio <= group_config["max"]:
            return group_name
    
    # Fallback classification
    if aspect_ratio < 0.95:
        return "portrait"
    elif aspect_ratio > 1.05:
        return "landscape"
    else:
        return "square"


def sort_resolutions(resolutions_dict: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Sort resolution keys based on configuration settings.
    Sort order: Category -> Aspect Ratio
    
    Args:
        resolutions_dict: Dictionary of resolutions with metadata
        
    Returns:
        Sorted list of resolution keys
    """
    display_config = config.get_section("display_settings")
    resolution_items = list(resolutions_dict.items())
    
    # Define sort order for categories
    category_order = {"sdxl": 0, "sd15": 1, "custom": 2}
    
    # Two-level sort: Category -> Aspect Ratio
    resolution_items.sort(key=lambda x: (
        category_order.get(x[1].get("category", "custom"), 2),  # Category priority
        x[1].get("aspect_ratio", 1.0)  # Aspect ratio (numerical)
    ))
    
    return [key for key, _ in resolution_items]


def filter_resolutions_by_category(resolutions_dict: Dict[str, Dict[str, Any]], 
                                   filter_category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Filter resolutions by category.
    
    Args:
        resolutions_dict: Dictionary of all resolutions
        filter_category: Category to filter by (sdxl, sd15, custom) or None for all
        
    Returns:
        Filtered dictionary of resolutions
    """
    if not filter_category:
        return resolutions_dict
    
    return {
        key: data for key, data in resolutions_dict.items()
        if data.get("category", "custom").lower() == filter_category.lower()
    }


# Note: filter_resolutions_by_aspect_group function removed as aspect group classification is no longer used


def get_resolution_statistics(resolutions_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate statistics about loaded resolutions.
    
    Args:
        resolutions_dict: Dictionary of resolutions
        
    Returns:
        Dictionary containing statistics
    """
    if not resolutions_dict:
        return {}
    
    stats = {
        "total_count": len(resolutions_dict),
        "categories": {},
        "resolution_ranges": {},
        "duplicates": []
    }
    
    # Count by categories
    for key, data in resolutions_dict.items():
        category = data.get("category", "custom")
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
    
    # Find resolution ranges
    pixel_counts = [data["pixel_count"] for data in resolutions_dict.values()]
    if pixel_counts:
        stats["resolution_ranges"] = {
            "min_pixels": min(pixel_counts),
            "max_pixels": max(pixel_counts),
            "avg_pixels": sum(pixel_counts) // len(pixel_counts)
        }
    
    # Detect duplicates (same width/height but different keys)
    resolution_pairs = {}
    for key, data in resolutions_dict.items():
        pair = (data["width"], data["height"])
        if pair in resolution_pairs:
            stats["duplicates"].append({
                "resolution": f"{data['width']}x{data['height']}",
                "keys": [resolution_pairs[pair], key]
            })
        else:
            resolution_pairs[pair] = key
    
    return stats


class ResolutionManager(ResolutionManagerInterface):
    """Manages resolution loading, caching, and processing."""
    
    def __init__(self, directory: Optional[str] = None):
        """
        Initialize ResolutionManager.
        
        Args:
            directory: Directory containing resolution JSON files. 
                      If None, uses the directory of this script.
        """
        self._directory = directory or os.path.dirname(os.path.realpath(__file__))
        self._cache_manager = CacheManager()
        self._resolution_dictionary: Optional[Dict[str, Dict[str, Any]]] = None
        self._usage_stats_manager: Optional['UsageStatsManager'] = None
    
    @property
    def usage_stats_manager(self) -> 'UsageStatsManager':
        """Get the usage stats manager, creating it if necessary."""
        if self._usage_stats_manager is None:
            try:
                from .usage_stats import UsageStatsManager
                self._usage_stats_manager = UsageStatsManager()
            except ImportError:
                # Create a dummy manager if import fails
                class DummyUsageManager:
                    def get_resolution_marks(self, resolution_key: str, config_manager=None) -> List[str]:
                        return []
                    def record_usage(self, resolution_key: str) -> None:
                        pass
                self._usage_stats_manager = DummyUsageManager()
        return self._usage_stats_manager
    
    @property
    def directory(self) -> str:
        """Get the resolution files directory."""
        return self._directory
    
    @property
    def resolution_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """Get the resolution dictionary, loading it if necessary."""
        if self._resolution_dictionary is None:
            self.load_resolutions()
        return self._resolution_dictionary
    
    def load_resolutions(self, force_reload: bool = False) -> None:
        """
        Load resolutions from JSON files.
        
        Args:
            force_reload: Force reload even if cache is valid
        """
        if not force_reload and self._cache_manager.is_cache_valid(self._directory):
            if config.get("logging", "log_resolution_loading"):
                logger.debug("Using cached resolution dictionary")
            return
        
        if config.get("logging", "log_resolution_loading"):
            logger.info(f"Loading resolutions from directory: {self._directory}")
        
        self._resolution_dictionary = load_resolutions_from_directory(self._directory)
        self._cache_manager.update_cache_timestamp(self._directory)
        
        # Log statistics
        if config.get("logging", "log_resolution_loading"):
            stats = get_resolution_statistics(self._resolution_dictionary)
            logger.info(f"Loaded {stats.get('total_count', 0)} resolutions")
            logger.info(f"Categories: {stats.get('categories', {})}")
            
            # Warn about duplicates
            if stats.get('duplicates'):
                logger.warning(f"Found {len(stats['duplicates'])} duplicate resolutions")
                for dup in stats['duplicates']:
                    logger.warning(f"Duplicate {dup['resolution']}: {dup['keys']}")
            
            # Debug individual resolutions
            for key, item in self._resolution_dictionary.items():
                logger.debug(f"Resolution: {key} [{item.get('category', 'custom')}] aspect_ratio:{item.get('aspect_ratio', 1.0):.3f}")
    
    def get_sorted_resolution_list(self) -> List[str]:
        """
        Get list of resolution keys sorted according to configuration.
        
        Returns:
            Sorted list of resolution keys with usage marks
        """
        base_list = sort_resolutions(self.resolution_dictionary)
        
        # Add usage marks if enabled
        display_config = config.get_section("display_settings")
        if not display_config.get("show_usage_marks", True):
            return base_list
        
        marked_list = []
        for resolution_key in base_list:
            marked_key = self._add_usage_marks(resolution_key)
            marked_list.append(marked_key)
        
        return marked_list
    
    def _add_usage_marks(self, resolution_key: str) -> str:
        """
        Add usage marks to a resolution key.
        
        Args:
            resolution_key: Original resolution key
            
        Returns:
            Resolution key with usage marks appended
        """
        display_config = config.get_section("display_settings")
        
        if not display_config.get("show_usage_marks", True):
            return resolution_key
        
        marks = self.usage_stats_manager.get_resolution_marks(resolution_key, config)
        
        if marks:
            marks_str = " " + "".join(marks)
            return f"{resolution_key}{marks_str}"
        
        return resolution_key
    
    def _remove_usage_marks(self, marked_resolution_key: str) -> str:
        """
        Remove usage marks from a resolution key to get the original key.
        
        Args:
            marked_resolution_key: Resolution key with usage marks (now at the end)
            
        Returns:
            Original resolution key without marks
        """
        display_config = config.get_section("display_settings")
        usage_marks = display_config.get("usage_marks", {})
        
        # Remove known marks from the end of the string
        clean_key = marked_resolution_key
        for mark in usage_marks.values():
            if clean_key.endswith(mark):
                clean_key = clean_key[:-len(mark)].rstrip()
        
        # Remove any remaining emoji/special characters at the end
        while clean_key and not clean_key[-1].isalnum() and clean_key[-1] != ')':
            clean_key = clean_key[:-1].rstrip()
        
        return clean_key
    
    def get_resolution_data(self, resolution_key: str) -> Optional[Dict[str, Any]]:
        """
        Get resolution data for a specific key.
        
        Args:
            resolution_key: Resolution key to look up (may include usage marks)
            
        Returns:
            Resolution data dictionary or None if not found
        """
        # Remove usage marks to get the original key
        clean_key = self._remove_usage_marks(resolution_key)
        return self.resolution_dictionary.get(clean_key)
    
    def record_resolution_usage(self, resolution_key: str) -> None:
        """
        Record usage of a resolution.
        
        Args:
            resolution_key: Resolution key that was used (may include usage marks)
        """
        # Remove usage marks to get the original key for recording
        clean_key = self._remove_usage_marks(resolution_key)
        self.usage_stats_manager.record_usage(clean_key)
    
    def add_favorite_resolution(self, resolution_key: str) -> bool:
        """
        Add resolution to favorites.
        
        Args:
            resolution_key: Resolution key to add (may include usage marks)
            
        Returns:
            True if added, False if already in favorites
        """
        clean_key = self._remove_usage_marks(resolution_key)
        return self.usage_stats_manager.add_favorite(clean_key)
    
    def remove_favorite_resolution(self, resolution_key: str) -> bool:
        """
        Remove resolution from favorites.
        
        Args:
            resolution_key: Resolution key to remove (may include usage marks)
            
        Returns:
            True if removed, False if not in favorites
        """
        clean_key = self._remove_usage_marks(resolution_key)
        return self.usage_stats_manager.remove_favorite(clean_key)
    
    def filter_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Filter resolutions by category.
        
        Args:
            category: Category to filter by (sdxl, sd15, custom)
            
        Returns:
            Filtered dictionary of resolutions
        """
        return filter_resolutions_by_category(self.resolution_dictionary, category)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded resolutions.
        
        Returns:
            Statistics dictionary
        """
        return get_resolution_statistics(self.resolution_dictionary)
    
    def invalidate_cache(self) -> None:
        """Invalidate the resolution cache."""
        self._cache_manager.invalidate_cache()
        self._resolution_dictionary = None
    
    def reload_resolutions(self) -> None:
        """Force reload resolutions from files."""
        self.invalidate_cache()
        self.load_resolutions(force_reload=True)


class SdxlEmptyLatentImage:
    """
    ComfyUI node for generating empty latent images with predefined resolutions.
    
    This node allows users to select from preconfigured resolutions loaded from JSON files,
    providing optimal settings for SDXL and other Stable Diffusion models.
    """
    _resolution_manager: Optional[ResolutionManagerInterface] = None
    _latent_generator: Optional[LatentGeneratorInterface] = None

    @classmethod
    def _get_resolution_manager(cls) -> ResolutionManagerInterface:
        """Get the resolution manager instance, creating it if necessary."""
        if cls._resolution_manager is None:
            cls._resolution_manager = ResolutionManager()
        return cls._resolution_manager
    
    @classmethod
    def _get_latent_generator(cls) -> LatentGeneratorInterface:
        """Get the latent generator instance, creating it if necessary."""
        if cls._latent_generator is None:
            try:
                from .latent_generator import ConfigurableLatentGenerator
                cls._latent_generator = ConfigurableLatentGenerator(config)
            except ImportError:
                # Fallback to inline implementation
                class FallbackGenerator(LatentGeneratorInterface):
                    def generate_latent(self, width: int, height: int, batch_size: int) -> Dict[str, Any]:
                        latent_config = config.get_section("latent_settings")
                        latent = torch.zeros([
                            batch_size,
                            latent_config.get("channels", 4),
                            height // latent_config.get("scale_factor", 8),
                            width // latent_config.get("scale_factor", 8),
                        ])
                        return {"samples": latent}
                
                cls._latent_generator = FallbackGenerator()
        return cls._latent_generator

    def __init__(self, device: str = "cpu") -> None:
        self.device = device
        # Ensure resolution manager is initialized
        self._get_resolution_manager()

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        resolution_manager = cls._get_resolution_manager()
        
        # Get sorted resolution list
        resolution_list = resolution_manager.get_sorted_resolution_list()

        if config.get("logging", "debug"):
            logger.debug(f"Available resolutions: {len(resolution_list)} items")

        batch_config = config.get_section("batch_settings")
        return {
            "required": {
                "resolution": (resolution_list,),
                "batch_size": ("INT", {
                    "default": batch_config["default_batch_size"], 
                    "min": batch_config["min_batch_size"], 
                    "max": batch_config["max_batch_size"]
                }),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"

    CATEGORY = "latent"

    def generate(self, resolution: str, batch_size: int = 1) -> Tuple[Dict[str, torch.Tensor]]:
        """
        Generate empty latent tensors with the specified resolution and batch size.
        
        Args:
            resolution: Resolution string key from the available options
            batch_size: Number of latent images to generate (default: 1)
            
        Returns:
            Tuple containing a dictionary with 'samples' key mapping to the latent tensor
            
        Raises:
            None - Errors are handled gracefully with fallback to default resolution
        """
        if config.get("logging", "debug"):
            logger.debug(f"Generating latent for resolution: {resolution}, batch_size: {batch_size}")

        try:
            resolution_manager = self._get_resolution_manager()
            resolution_data = resolution_manager.get_resolution_data(resolution)
            
            if resolution_data is None:
                raise ValueError(f"Resolution '{resolution}' not found in dictionary")
            
            batch_config = config.get_section("batch_settings")
            if batch_size < batch_config["min_batch_size"] or batch_size > batch_config["max_batch_size"]:
                raise ValueError(f"Batch size {batch_size} outside valid range [{batch_config['min_batch_size']}, {batch_config['max_batch_size']}]")
            
            width = resolution_data["width"]
            height = resolution_data["height"]
            
            # Record usage statistics
            resolution_manager.record_resolution_usage(resolution)
            
            latent_generator = self._get_latent_generator()
            latent_result = latent_generator.generate_latent(width, height, batch_size)
            return (latent_result,)
            
        except Exception as e:
            logger.error(f"Error generating latent: {e}")
            # Fallback to a default resolution
            latent_config = config.get_section("latent_settings")
            fallback_size = latent_config["fallback_resolution"]
            
            try:
                latent_generator = self._get_latent_generator()
                fallback_result = latent_generator.generate_latent(fallback_size, fallback_size, batch_size)
                return (fallback_result,)
            except Exception as fallback_error:
                logger.error(f"Error in fallback latent generation: {fallback_error}")
                # Ultimate fallback with hardcoded values
                fallback_latent = torch.zeros([batch_size, 4, 128, 128])
                return ({"samples": fallback_latent},)


NODE_CLASS_MAPPINGS = {
    "SDXL Empty Latent Image": SdxlEmptyLatentImage,
}
