"""
Usage statistics and favorites management for resolutions.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict


class UsageStatsManager:
    """Manages resolution usage statistics, favorites, and recent usage."""
    
    def __init__(self, stats_file: str = "usage_stats.json"):
        """
        Initialize usage stats manager.
        
        Args:
            stats_file: Path to the stats JSON file
        """
        self.stats_file = stats_file
        self._stats_data: Optional[Dict[str, Any]] = None
        self._load_stats()
    
    def _get_stats_file_path(self) -> str:
        """Get full path to stats file."""
        current_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(current_dir, self.stats_file)
    
    def _load_stats(self) -> None:
        """Load usage statistics from JSON file."""
        stats_path = self._get_stats_file_path()
        
        default_stats = {
            "favorites": [],
            "usage_stats": {},
            "recent_usage": []
        }
        
        try:
            if os.path.exists(stats_path):
                with open(stats_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # Merge with defaults to handle missing keys
                    self._stats_data = {**default_stats, **loaded_data}
            else:
                self._stats_data = default_stats
        except Exception as e:
            print(f"Warning: Could not load usage stats: {e}")
            self._stats_data = default_stats
    
    def _save_stats(self) -> None:
        """Save usage statistics to JSON file."""
        if self._stats_data is None:
            return
            
        try:
            stats_path = self._get_stats_file_path()
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(self._stats_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save usage stats: {e}")
    
    def record_usage(self, resolution_key: str) -> None:
        """
        Record usage of a resolution.
        
        Args:
            resolution_key: Resolution key that was used
        """
        if self._stats_data is None:
            return
            
        current_time = datetime.now().isoformat()
        
        # Update usage statistics
        usage_stats = self._stats_data.get("usage_stats", {})
        if resolution_key not in usage_stats:
            usage_stats[resolution_key] = {
                "count": 0,
                "first_used": current_time,
                "last_used": current_time
            }
        
        usage_stats[resolution_key]["count"] += 1
        usage_stats[resolution_key]["last_used"] = current_time
        self._stats_data["usage_stats"] = usage_stats
        
        # Update recent usage (keep last 10 items)
        recent_usage = self._stats_data.get("recent_usage", [])
        
        # Remove any existing entry for this resolution
        recent_usage = [item for item in recent_usage if item.get("resolution") != resolution_key]
        
        # Add new entry at the beginning
        recent_usage.insert(0, {
            "resolution": resolution_key,
            "timestamp": current_time
        })
        
        # Keep only the last 10 items
        self._stats_data["recent_usage"] = recent_usage[:10]
        
        self._save_stats()
    
    def add_favorite(self, resolution_key: str) -> bool:
        """
        Add resolution to favorites.
        
        Args:
            resolution_key: Resolution key to add to favorites
            
        Returns:
            True if added, False if already in favorites
        """
        if self._stats_data is None:
            return False
            
        favorites = set(self._stats_data.get("favorites", []))
        if resolution_key in favorites:
            return False
            
        favorites.add(resolution_key)
        self._stats_data["favorites"] = list(favorites)
        self._save_stats()
        return True
    
    def remove_favorite(self, resolution_key: str) -> bool:
        """
        Remove resolution from favorites.
        
        Args:
            resolution_key: Resolution key to remove from favorites
            
        Returns:
            True if removed, False if not in favorites
        """
        if self._stats_data is None:
            return False
            
        favorites = set(self._stats_data.get("favorites", []))
        if resolution_key not in favorites:
            return False
            
        favorites.remove(resolution_key)
        self._stats_data["favorites"] = list(favorites)
        self._save_stats()
        return True
    
    def is_favorite(self, resolution_key: str) -> bool:
        """Check if resolution is in favorites."""
        if self._stats_data is None:
            return False
        return resolution_key in self._stats_data.get("favorites", [])
    
    def get_favorites(self) -> List[str]:
        """Get list of favorite resolutions."""
        if self._stats_data is None:
            return []
        return self._stats_data.get("favorites", [])
    
    def get_usage_count(self, resolution_key: str) -> int:
        """Get usage count for a resolution."""
        if self._stats_data is None:
            return 0
        usage_stats = self._stats_data.get("usage_stats", {})
        return usage_stats.get(resolution_key, {}).get("count", 0)
    
    def get_recent_resolutions(self, limit: int = 5) -> List[str]:
        """
        Get recently used resolutions.
        
        Args:
            limit: Maximum number of recent resolutions to return
            
        Returns:
            List of recently used resolution keys
        """
        if self._stats_data is None:
            return []
            
        recent_usage = self._stats_data.get("recent_usage", [])
        return [item["resolution"] for item in recent_usage[:limit]]
    
    def get_frequently_used(self, limit: int = 5, min_count: int = 2) -> List[str]:
        """
        Get frequently used resolutions.
        
        Args:
            limit: Maximum number of resolutions to return
            min_count: Minimum usage count to be considered frequent
            
        Returns:
            List of frequently used resolution keys, sorted by usage count
        """
        if self._stats_data is None:
            return []
            
        usage_stats = self._stats_data.get("usage_stats", {})
        
        # Filter by minimum count and sort by usage
        frequent_items = [
            (key, data["count"]) 
            for key, data in usage_stats.items() 
            if data["count"] >= min_count
        ]
        
        # Sort by count (descending) and take top items
        frequent_items.sort(key=lambda x: x[1], reverse=True)
        return [key for key, count in frequent_items[:limit]]
    
    def get_resolution_marks(self, resolution_key: str, config_manager=None) -> List[str]:
        """
        Get display marks for a resolution based on its status.
        
        Args:
            resolution_key: Resolution key to get marks for
            config_manager: Configuration manager for getting display settings
            
        Returns:
            List of mark strings to display
        """
        marks = []
        
        # Get configuration settings
        if config_manager:
            display_config = config_manager.get_section("display_settings")
            usage_marks = display_config.get("usage_marks", {
                "favorite": "★",
                "frequent": "🔥", 
                "recent": "🕒"
            })
            frequent_threshold = display_config.get("frequent_threshold", 3)
            recent_limit = display_config.get("recent_limit", 5)
        else:
            # Fallback defaults
            usage_marks = {"favorite": "★", "frequent": "🔥", "recent": "🕒"}
            frequent_threshold = 3
            recent_limit = 5
        
        # Check if favorite
        if self.is_favorite(resolution_key):
            marks.append(usage_marks.get("favorite", "★"))
        
        # Check if frequently used
        frequently_used = self.get_frequently_used(limit=20, min_count=frequent_threshold)
        if resolution_key in frequently_used:
            marks.append(usage_marks.get("frequent", "🔥"))
        
        # Check if recently used
        recent = self.get_recent_resolutions(limit=recent_limit)
        if resolution_key in recent:
            marks.append(usage_marks.get("recent", "🕒"))
        
        return marks
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get overall usage statistics.
        
        Returns:
            Dictionary with usage statistics summary
        """
        if self._stats_data is None:
            return {}
        
        usage_stats = self._stats_data.get("usage_stats", {})
        
        total_usage = sum(data.get("count", 0) for data in usage_stats.values())
        unique_resolutions = len(usage_stats)
        favorites_count = len(self._stats_data.get("favorites", []))
        
        # Find most used resolution
        most_used = None
        max_count = 0
        for key, data in usage_stats.items():
            count = data.get("count", 0)
            if count > max_count:
                max_count = count
                most_used = key
        
        return {
            "total_usage": total_usage,
            "unique_resolutions": unique_resolutions,
            "favorites_count": favorites_count,
            "most_used_resolution": most_used,
            "most_used_count": max_count
        }
    
    def cleanup_old_entries(self, days: int = 30) -> None:
        """
        Clean up old usage entries.
        
        Args:
            days: Remove entries older than this many days
        """
        if self._stats_data is None:
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        # Clean recent usage
        recent_usage = self._stats_data.get("recent_usage", [])
        self._stats_data["recent_usage"] = [
            item for item in recent_usage 
            if item.get("timestamp", "") > cutoff_iso
        ]
        
        # Optionally clean usage stats (commented out to preserve long-term data)
        # usage_stats = self._stats_data.get("usage_stats", {})
        # self._stats_data["usage_stats"] = {
        #     key: data for key, data in usage_stats.items()
        #     if data.get("last_used", "") > cutoff_iso
        # }
        
        self._save_stats()