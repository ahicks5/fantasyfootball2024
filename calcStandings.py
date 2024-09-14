import json

def load_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def calculate_team_totals(fantasy_data):
    """Calculate the total fantasy points for each team, excluding bench players."""
    team_totals = {}
    team_names = {}

    for team_id, players in fantasy_data.items():
        total_points = sum(player["fantasy_points"] for player in players if player["lineup_pos"] != "BN")
        team_name = players[0]["team_name"]  # Assume all players in a team have the same team_name
        team_totals[team_id] = total_points
        team_names[team_id] = team_name

    return team_totals, team_names

def calculate_win_loss_records(schedule_data, team_totals, team_names):
    """Calculate win-loss records and update team stats."""
    team_records = {team_names[team_id]: {"wins": 0, "losses": 0, "ties": 0, "PF": 0, "PA": 0, "streak": "", "expected_wins": 0, "expected_losses": 0} for team_id in team_names}

    week = "1"  # Assume we are only dealing with Week 1 data

    matchups = schedule_data[week]
    for matchup in matchups:
        team1_id = matchup["team1_id"]
        team2_id = matchup["team2_id"]

        team1_score = team_totals.get(team1_id, 0)
        team2_score = team_totals.get(team2_id, 0)

        team1_name = team_names[team1_id]
        team2_name = team_names[team2_id]

        # Update Points For (PF) and Points Against (PA)
        team_records[team1_name]["PF"] += team1_score
        team_records[team1_name]["PA"] += team2_score
        team_records[team2_name]["PF"] += team2_score
        team_records[team2_name]["PA"] += team1_score

        # Update wins, losses, and streaks
        if team1_score > team2_score:
            team_records[team1_name]["wins"] += 1
            team_records[team2_name]["losses"] += 1
            team_records[team1_name]["streak"] = "W-1"
            team_records[team2_name]["streak"] = "L-1"
        elif team2_score > team1_score:
            team_records[team2_name]["wins"] += 1
            team_records[team1_name]["losses"] += 1
            team_records[team2_name]["streak"] = "W-1"
            team_records[team1_name]["streak"] = "L-1"
        else:
            team_records[team1_name]["ties"] += 1
            team_records[team2_name]["ties"] += 1
            team_records[team1_name]["streak"] = "T-1"
            team_records[team2_name]["streak"] = "T-1"

    return team_records

def calculate_expected_record(team_totals, team_names, team_records):
    """Calculate expected wins and losses for each team."""
    for team_id, team_name in team_names.items():
        wins_against_others = 0
        losses_against_others = 0
        team_score = team_totals[team_id]

        for other_team_id, other_team_score in team_totals.items():
            if team_id == other_team_id:
                continue  # Skip comparison with itself
            if team_score > other_team_score:
                wins_against_others += 1
            elif team_score < other_team_score:
                losses_against_others += 1

        total_teams = len(team_totals) - 1  # Exclude the current team itself

        if total_teams > 0:
            win_percentage = wins_against_others / total_teams
            loss_percentage = losses_against_others / total_teams
            team_records[team_name]["expected_wins"] = win_percentage
            team_records[team_name]["expected_losses"] = loss_percentage

def save_standings_to_json(standings, output_file):
    """Save the standings data to a JSON file."""
    with open(output_file, 'w') as file:
        json.dump(standings, file, indent=4)

def main():
    # Load data
    fantasy_data = load_data('league_data_week_1.json')
    schedule_data = load_data('league_schedule_weeks_1_to_14.json')

    # Calculate team totals and names
    team_totals, team_names = calculate_team_totals(fantasy_data)

    # Calculate win-loss records
    team_records = calculate_win_loss_records(schedule_data, team_totals, team_names)

    # Calculate expected wins and losses
    calculate_expected_record(team_totals, team_names, team_records)

    # Prepare the standings sorted by the number of wins, then by points for (PF)
    sorted_standings = sorted(team_records.items(), key=lambda x: (x[1]["wins"], x[1]["PF"]), reverse=True)

    # Save the standings to a JSON file
    save_standings_to_json(sorted_standings, 'standings.json')

if __name__ == "__main__":
    main()
