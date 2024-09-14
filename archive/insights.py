import pandas as pd

def safe_float_conversion(value):
    """
    Safely converts a value to a float. Returns 0.0 if the conversion is not possible.

    Args:
        value: The value to convert.

    Returns:
        float: The converted float value, or 0.0 if conversion fails.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def extract_starter_data(league_data):
    """
    Extracts the data for starting players from the league data.

    Args:
        league_data (dict): The league data with team IDs as keys and player data as values.

    Returns:
        pd.DataFrame: A DataFrame containing the extracted starter data.
    """
    starters = []
    for team in league_data.values():
        for player in team:
            # Include only starters, excluding bench and IR spots
            if player['lineup_pos'] not in ['BN', 'IR']:
                actual_fantasy_points = safe_float_conversion(player.get('fantasy_points', 0.0))
                projected_fantasy_points = safe_float_conversion(player.get('projected_fantasy_points', 0.0))
                points_diff = actual_fantasy_points - projected_fantasy_points

                # Ensure the position is captured, even if it's missing
                position = player.get('position', 'Unknown Position')

                starters.append({
                    'team_name': player.get('team_name', 'Unknown Team'),
                    'player_name': player.get('name', 'Unknown Player'),
                    'position': position,  # Include position here
                    'actual_fantasy_points': actual_fantasy_points,
                    'projected_fantasy_points': projected_fantasy_points,
                    'points_diff': points_diff,
                })
    return pd.DataFrame(starters)


def extract_bench_data(league_data):
    """
    Extracts the data for bench players from the league data.

    Args:
        league_data (dict): The league data with team IDs as keys and player data as values.

    Returns:
        pd.DataFrame: A DataFrame containing the extracted bench data.
    """
    bench = []
    for team in league_data.values():
        for player in team:
            # Include only bench spots
            if player['lineup_pos'] == 'BN':
                actual_fantasy_points = safe_float_conversion(player.get('fantasy_points', 0.0))
                # Ensure the position is captured, even if it's missing
                position = player.get('position', 'Unknown Position')
                bench.append({
                    'team_name': player.get('team_name', 'Unknown Team'),
                    'player_name': player.get('name', 'Unknown Player'),
                    'actual_fantasy_points': actual_fantasy_points,
                    'position': position,  # Include position here
                })
    return pd.DataFrame(bench)


def generate_insights(league_data):
    starters_df = extract_starter_data(league_data)
    bench_df = extract_bench_data(league_data)

    # Team with most projected points (starters only)
    team_proj_points = starters_df.groupby('team_name')['projected_fantasy_points'].sum().reset_index()

    # Team with most actual points (starters only)
    team_actual_points = starters_df.groupby('team_name')['actual_fantasy_points'].sum().reset_index()

    # Merge the dataframes to include projected points along with actual points and differences
    combined_df = pd.merge(team_actual_points, team_proj_points, on='team_name')
    combined_df['points_diff'] = combined_df['actual_fantasy_points'] - combined_df['projected_fantasy_points']

    # Teams with the biggest difference from projected points, both positive and negative
    biggest_pos_diff = combined_df.nlargest(5, 'points_diff').to_dict('records')
    biggest_neg_diff = combined_df.nsmallest(5, 'points_diff').to_dict('records')

    # Which bench did the best
    bench_points = bench_df.groupby('team_name')['actual_fantasy_points'].sum().reset_index().sort_values(by='actual_fantasy_points', ascending=False).to_dict('records')

    top_positive_contributors = starters_df.sort_values(by='points_diff', ascending=False).groupby('team_name').head(3)[
        ['team_name', 'player_name', 'position', 'actual_fantasy_points', 'projected_fantasy_points',
         'points_diff']].to_dict('records')

    top_negative_contributors = starters_df.sort_values(by='points_diff', ascending=True).groupby('team_name').head(3)[
        ['team_name', 'player_name', 'position', 'actual_fantasy_points', 'projected_fantasy_points',
         'points_diff']].to_dict('records')

    insights = {
        'team_proj_points': team_proj_points.to_dict('records'),
        'team_actual_points': team_actual_points.to_dict('records'),
        'biggest_pos_diff': biggest_pos_diff,  # Now includes projected points
        'biggest_neg_diff': biggest_neg_diff,  # Now includes projected points
        'bench_points': bench_points,
        'top_positive_contributors': top_positive_contributors,  # Adding positive contributors
        'top_negative_contributors': top_negative_contributors,  # Adding negative contributors
    }

    return insights



# Example usage for testing the insights generation
if __name__ == "__main__":
    # Example league data based on the output you provided from the yahoo_data.py script
    league_data = {
        1: [
            {'lineup_pos': 'QB', 'name': 'Patrick Mahomes', 'team': 'KC', 'position': 'QB', 'bye_week': '6', 'fantasy_points': '16.14', 'projected_fantasy_points': '21.03', 'team_name': 'Obi-Jan Kenobi\ue002'},
            {'lineup_pos': 'WR', 'name': 'Brandon Aiyuk', 'team': 'SF', 'position': 'WR', 'bye_week': '9', 'fantasy_points': '–', 'projected_fantasy_points': '12.19', 'team_name': 'Obi-Jan Kenobi\ue002'},
            {'lineup_pos': 'BN', 'name': 'Bijan Robinson', 'team': 'Atl', 'position': 'RB', 'bye_week': '12', 'fantasy_points': '16.10', 'projected_fantasy_points': '16.31', 'team_name': 'Obi-Jan Kenobi\ue002'},
            # Add more players as needed
        ],
        2: [
            {'lineup_pos': 'QB', 'name': 'Lamar Jackson', 'team': 'Bal', 'position': 'QB', 'bye_week': '14', 'fantasy_points': '25.12', 'projected_fantasy_points': '20.32', 'team_name': 'Sandusky’s Tight Ends\ue002'},
            {'lineup_pos': 'WR', 'name': 'Mike Evans', 'team': 'TB', 'position': 'WR', 'bye_week': '11', 'fantasy_points': '23.10', 'projected_fantasy_points': '13.44', 'team_name': 'Sandusky’s Tight Ends\ue002'},
            {'lineup_pos': 'BN', 'name': 'Najee Harris', 'team': 'Pit', 'position': 'RB', 'bye_week': '9', 'fantasy_points': '8.90', 'projected_fantasy_points': '10.23', 'team_name': 'Sandusky’s Tight Ends\ue002'},
            # Add more players as needed
        ],
        # Add more teams as needed
    }

    # Generate insights based on the example league data
    insights = generate_insights(league_data)

    # Print the insights to understand the output
    print("Team Projected Points:", insights['team_proj_points'])
    print("Team Actual Points:", insights['team_actual_points'])
    print("Biggest Positive Differences:", insights['biggest_pos_diff'])
    print("Biggest Negative Differences:", insights['biggest_neg_diff'])
    print("Bench Points:", insights['bench_points'])
