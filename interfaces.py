"""
Interface definitions for better testability and extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ResolutionLoaderInterface(ABC):
    """Interface for loading resolution data from various sources."""
    
    @abstractmethod
    def load_resolutions(self, source: str) -> Dict[str, Dict[str, Any]]:
        """
        Load resolutions from a source.
        
        Args:
            source: Source identifier (file path, URL, etc.)
            
        Returns:
            Dictionary of resolution data
        """
        pass


class CacheInterface(ABC):
    """Interface for caching mechanisms."""
    
    @abstractmethod
    def is_valid(self, key: str) -> bool:
        """Check if cache entry is valid."""
        pass
    
    @abstractmethod
    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry or all entries."""
        pass
    
    @abstractmethod
    def update(self, key: str, data: Any) -> None:
        """Update cache entry."""
        pass


class ResolutionManagerInterface(ABC):
    """Interface for resolution management."""
    
    @abstractmethod
    def load_resolutions(self, force_reload: bool = False) -> None:
        """Load resolutions from source."""
        pass
    
    @abstractmethod
    def get_sorted_resolution_list(self) -> List[str]:
        """Get sorted list of resolution keys."""
        pass
    
    @abstractmethod
    def get_resolution_data(self, resolution_key: str) -> Optional[Dict[str, Any]]:
        """Get resolution data for a specific key."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded resolutions."""
        pass


class LatentGeneratorInterface(ABC):
    """Interface for latent image generation."""
    
    @abstractmethod
    def generate_latent(self, width: int, height: int, batch_size: int) -> Dict[str, Any]:
        """
        Generate latent tensor.
        
        Args:
            width: Image width
            height: Image height  
            batch_size: Number of images in batch
            
        Returns:
            Dictionary containing latent tensor
        """
        pass