"""
Debug utility to check usage statistics and display information.
"""

import json
import os
from usage_stats import UsageStatsManager

def print_usage_debug():
    """Print detailed usage statistics for debugging."""
    print("=== Usage Statistics Debug Info ===")
    
    try:
        # Initialize usage stats manager
        stats_manager = UsageStatsManager()
        
        # Print overall statistics
        overall_stats = stats_manager.get_usage_statistics()
        print(f"\n[Overall Statistics]")
        print(f"  Total Usage: {overall_stats.get('total_usage', 0)}")
        print(f"  Unique Resolutions: {overall_stats.get('unique_resolutions', 0)}")
        print(f"  Favorites Count: {overall_stats.get('favorites_count', 0)}")
        print(f"  Most Used Resolution: {overall_stats.get('most_used_resolution', 'None')}")
        print(f"  Max Usage Count: {overall_stats.get('most_used_count', 0)}")
        
        # Print detailed usage for each resolution
        print(f"\n[Resolution Usage Details]")
        usage_data = stats_manager._stats_data.get('usage_stats', {})
        
        if not usage_data:
            print("  No usage data found")
        else:
            # Sort by usage count
            sorted_usage = sorted(usage_data.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for resolution, data in sorted_usage:
                count = data['count']
                last_used = data['last_used'][:19]  # Remove microseconds
                marks = stats_manager.get_resolution_marks(resolution)
                marks_str = "".join(marks) if marks else "None"
                
                print(f"  - {resolution}")
                print(f"    Count: {count}, Last Used: {last_used}, Marks: {marks_str}")
        
        # Print current configuration
        print(f"\n[Configuration Settings]")
        from sdxl_empty_latent import config
        display_config = config.get_section("display_settings")
        
        print(f"  Show Usage Marks: {display_config.get('show_usage_marks', True)}")
        print(f"  Frequent Threshold: {display_config.get('frequent_threshold', 3)}")
        print(f"  Recent Limit: {display_config.get('recent_limit', 5)}")
        
        usage_marks = display_config.get('usage_marks', {})
        print(f"  Mark Settings:")
        print(f"    Favorite: {usage_marks.get('favorite', 'Star')}")
        print(f"    Frequent: {usage_marks.get('frequent', 'Fire')}")
        print(f"    Recent: {usage_marks.get('recent', 'Clock')}")
        
        # Print recent usage
        recent_list = stats_manager.get_recent_resolutions()
        print(f"\n[Recent Usage] (Top {len(recent_list)} items)")
        if not recent_list:
            print("  None")
        else:
            for i, resolution in enumerate(recent_list, 1):
                print(f"  {i}. {resolution}")
        
        # Print frequently used (with current threshold)
        frequent_threshold = display_config.get('frequent_threshold', 3)
        frequently_used = stats_manager.get_frequently_used(min_count=frequent_threshold)
        print(f"\n[Frequently Used] (Threshold: {frequent_threshold}+ times)")
        if not frequently_used:
            print("  None (No resolutions reached the threshold)")
        else:
            for i, resolution in enumerate(frequently_used, 1):
                count = usage_data.get(resolution, {}).get('count', 0)
                print(f"  {i}. {resolution} ({count} times)")
        
        # Print favorites
        favorites = stats_manager.get_favorites()
        print(f"\n[Favorites]")
        if not favorites:
            print("  None")
        else:
            for i, resolution in enumerate(favorites, 1):
                print(f"  {i}. {resolution}")
        
        print(f"\n[Tips]")
        if overall_stats.get('most_used_count', 0) < frequent_threshold:
            print(f"  To show frequent marks, use the same resolution {frequent_threshold}+ times")
            print(f"  Current max usage count: {overall_stats.get('most_used_count', 0)}")
        
        print(f"  To adjust settings, modify 'frequent_threshold' in config.json")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print_usage_debug()