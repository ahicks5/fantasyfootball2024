import json
from week_insights import get_weekly_insights

CACHE_FILE = 'insights_cache.json'

def refresh_cache(league_id, week_start, week_end, team_count=12):
    """
    Refresh the insights cache for a range of weeks.

    Args:
        league_id (str): The ID of the league.
        week_start (int): The starting week number.
        week_end (int): The ending week number.
        team_count (int): The number of teams in the league. Default is 12.
    """
    # Initialize an empty dictionary to store cached data
    cached_data = {}

    # Loop through each week in the specified range
    for week_num in range(week_start, week_end + 1):
        print(f"Fetching data for week {week_num}...")
        try:
            # Fetch insights data for the specific week
            insights_data = get_weekly_insights(league_id, week_num, team_count)
            # Store the fetched insights data in the cached_data dictionary
            cached_data[str(week_num)] = insights_data
        except Exception as e:
            # Handle any errors that occur during data fetching
            print(f"Error fetching data for week {week_num}: {e}")

    # Save the refreshed data to the cache file
    try:
        with open(CACHE_FILE, 'w') as file:
            json.dump(cached_data, file, indent=4)
        print(f"Cache refreshed for weeks {week_start} to {week_end}.")
    except Exception as e:
        # Handle any errors that occur during the cache-saving process
        print(f"Error saving cache to {CACHE_FILE}: {e}")

if __name__ == "__main__":
    # Example league ID and week range for testing purposes
    league_id = "22030"  # Replace with your actual league ID
    week_start = 1  # The first week to refresh
    week_end = 1  # The last week to refresh (e.g., if the season is 17 weeks long)

    # Refresh the cache for the specified range of weeks
    refresh_cache(league_id, week_start, week_end)
