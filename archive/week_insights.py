from yahoo_data import YahooFantasyAPI
from insights import generate_insights


def get_weekly_insights(league_id, week_num, team_count=12):
    """
    Retrieves weekly insights for a given fantasy football league.

    Args:
        league_id (str): The ID of the fantasy football league.
        week_num (int): The week number for which to retrieve insights.
        team_count (int): The number of teams in the league. Default is 12.

    Returns:
        dict: A dictionary containing various insights for the specified week.
    """
    # Initialize the YahooFantasyAPI to interact with the Yahoo Fantasy Football website
    yahoo_api = YahooFantasyAPI()

    # Initialize a dictionary to hold all the data for the league
    league_data = {}

    # Loop over each team in the league and gather player data
    for team_id in range(1, team_count + 1):
        # Fetch the roster data for the specific team and week
        team_data = yahoo_api.get_team_roster_by_week(league_id, team_id, week_num)

        # Store the team data in the league_data dictionary
        league_data[team_id] = team_data

    # Close the YahooFantasyAPI connection after gathering data
    yahoo_api.close()

    # Generate insights from the collected league data
    insights = generate_insights(league_data)

    # Return the generated insights
    return insights


if __name__ == "__main__":
    # Example league ID and week number for testing purposes
    league_id = "22030"
    week_num = 1
    team_count = 2  # Adjust based on the number of teams you want to test with

    # Fetch weekly insights for the given league and week
    insights = get_weekly_insights(league_id, week_num, team_count)

    # Print the insights to understand the output
    print("Generated Insights:")
    print("Team Projected Points:", insights['team_proj_points'])
    print("Team Actual Points:", insights['team_actual_points'])
    print("Biggest Positive Differences:", insights['biggest_pos_diff'])
    print("Biggest Negative Differences:", insights['biggest_neg_diff'])
    print("Bench Points:", insights['bench_points'])
