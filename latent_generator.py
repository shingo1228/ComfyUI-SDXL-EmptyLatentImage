"""
Latent image generation functionality separated for better testability.
"""

import torch
from typing import Dict, Any

try:
    from .interfaces import LatentGeneratorInterface
except ImportError:
    # Fallback for when interfaces module is not available
    from abc import ABC, abstractmethod
    
    class LatentGeneratorInterface(ABC):
        @abstractmethod
        def generate_latent(self, width: int, height: int, batch_size: int) -> Dict[str, Any]: pass


class StandardLatentGenerator(LatentGeneratorInterface):
    """Standard latent image generator for Stable Diffusion models."""
    
    def __init__(self, channels: int = 4, scale_factor: int = 8):
        """
        Initialize latent generator.
        
        Args:
            channels: Number of latent channels (typically 4 for SD models)
            scale_factor: Scaling factor from image to latent space (typically 8)
        """
        self.channels = channels
        self.scale_factor = scale_factor
    
    def generate_latent(self, width: int, height: int, batch_size: int) -> Dict[str, Any]:
        """
        Generate latent tensor for given dimensions.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            batch_size: Number of images in batch
            
        Returns:
            Dictionary containing the latent tensor under 'samples' key
        """
        latent = torch.zeros([
            batch_size,
            self.channels,
            height // self.scale_factor,
            width // self.scale_factor,
        ])
        
        return {"samples": latent}


class ConfigurableLatentGenerator(LatentGeneratorInterface):
    """Latent generator that reads configuration from config object."""
    
    def __init__(self, config_manager):
        """
        Initialize with config manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
    
    def generate_latent(self, width: int, height: int, batch_size: int) -> Dict[str, Any]:
        """
        Generate latent tensor using configuration settings.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            batch_size: Number of images in batch
            
        Returns:
            Dictionary containing the latent tensor under 'samples' key
        """
        latent_config = self.config_manager.get_section("latent_settings")
        
        latent = torch.zeros([
            batch_size,
            latent_config.get("channels", 4),
            height // latent_config.get("scale_factor", 8),
            width // latent_config.get("scale_factor", 8),
        ])
        
        return {"samples": latent}