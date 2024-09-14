import json

class FantasyLeagueAnalyzer:
    def __init__(self, data):
        """
        Initializes the FantasyLeagueAnalyzer with the league data.

        Args:
            data (dict): The league data containing teams and player information.
        """
        self.data = data  # Raw data input
        self.teams = {}   # Processed team data

        # Lineup requirements (number of players required in each position)
        self.lineup_requirements = {
            'QB': 1,
            'RB': 2,
            'WR': 2,
            'TE': 1,
            'W/R/T': 1,  # Flex position
            'K': 1,
            'DEF': 1
        }

        # Positions eligible for flex
        self.flex_positions = ['RB', 'WR', 'TE']

        # Process the raw data to structure it per team
        self.process_data()

    def process_data(self):
        """
        Processes the raw data to structure it per team for easier analysis.
        """
        for team_id, players in self.data.items():
            team_name = players[0]['team_name']
            self.teams[team_id] = {
                'team_name': team_name,
                'players': players,
                'lineups': {
                    'chosen': [],
                    'optimal_projected': [],
                    'optimal_actual': []
                },
                'metrics': {}
            }

    def calculate_optimal_lineup(self, team_id, use_projection=True):
        """
        Calculates the optimal lineup for a team based on projections or actual points.

        Args:
            team_id (int): The ID of the team.
            use_projection (bool): If True, use projected points; else, use actual points.
        """
        team = self.teams[team_id]
        players = team['players']

        # Sort players based on projected or actual points
        key = 'projected_fantasy_points' if use_projection else 'fantasy_points'
        sorted_players = sorted(players, key=lambda x: x[key], reverse=True)

        lineup = []
        positions_filled = {pos: 0 for pos in self.lineup_requirements.keys()}
        flex_filled = 0

        for player in sorted_players:
            player_pos = player['position']
            lineup_pos = player['lineup_pos']

            # Skip injured reserve players
            if lineup_pos == 'IR':
                continue

            # Check if position is needed in lineup
            if positions_filled.get(player_pos, 0) < self.lineup_requirements.get(player_pos, 0):
                lineup.append(player)
                positions_filled[player_pos] += 1
            # Fill flex position if eligible
            elif flex_filled < self.lineup_requirements['W/R/T'] and player_pos in self.flex_positions:
                lineup.append(player)
                flex_filled += 1
            # Check if special positions (K, DEF) are needed
            elif player_pos in ['K', 'DEF'] and positions_filled[player_pos] < self.lineup_requirements[player_pos]:
                lineup.append(player)
                positions_filled[player_pos] += 1

            # Check if lineup is complete
            if len(lineup) == sum(self.lineup_requirements.values()):
                break

        # Store the lineup
        lineup_type = 'optimal_projected' if use_projection else 'optimal_actual'
        team['lineups'][lineup_type] = lineup

    def calculate_actual_lineup(self, team_id):
        """
        Extracts the actual lineup chosen by the manager for a team.

        Args:
            team_id (int): The ID of the team.
        """
        team = self.teams[team_id]
        players = team['players']

        lineup = [player for player in players if player['lineup_pos'] not in ['BN', 'IR']]

        # Ensure the lineup meets the requirements
        if len(lineup) != sum(self.lineup_requirements.values()):
            # Adjust lineup if necessary (could be due to incomplete data)
            lineup = lineup[:sum(self.lineup_requirements.values())]

        team['lineups']['chosen'] = lineup

    def calculate_team_metrics(self, team_id):
        """
        Calculates basic metrics for a team to assess managerial performance.

        Args:
            team_id (int): The ID of the team.
        """
        team = self.teams[team_id]
        metrics = {}

        # Total points for each lineup
        chosen_lineup = team['lineups']['chosen']
        chosen_points = sum(player['fantasy_points'] for player in chosen_lineup)
        optimal_projected_lineup = team['lineups']['optimal_projected']
        optimal_projected_points = sum(player['fantasy_points'] for player in optimal_projected_lineup)
        optimal_actual_lineup = team['lineups']['optimal_actual']
        optimal_actual_points = sum(player['fantasy_points'] for player in optimal_actual_lineup)

        # Calculate differences
        metrics['chosen_vs_optimal_actual'] = optimal_actual_points - chosen_points
        metrics['chosen_vs_optimal_projected'] = optimal_projected_points - chosen_points
        metrics['optimal_projected_vs_optimal_actual'] = optimal_actual_points - optimal_projected_points
        metrics['lineup_efficiency'] = (chosen_points / optimal_actual_points) * 100 if optimal_actual_points > 0 else 0
        metrics['overperformance'] = chosen_points - sum(player['projected_fantasy_points'] for player in chosen_lineup)

        # Calculate percentage of players that beat projections in the chosen lineup
        beat_projection = [player for player in chosen_lineup if player['fantasy_points'] > player['projected_fantasy_points']]
        metrics['percent_players_beat_projection'] = (len(beat_projection) / len(chosen_lineup)) * 100 if chosen_lineup else 0
        metrics['percent_players_did_not_beat_projection'] = 100 - metrics['percent_players_beat_projection']

        # Enhanced calculations: Magnitude of overperformance/underperformance
        total_percent_diff = 0
        total_overperf_percent_diff = 0
        total_underperf_percent_diff = 0
        overperf_count = 0
        underperf_count = 0

        for player in chosen_lineup:
            proj = player['projected_fantasy_points']
            actual = player['fantasy_points']
            if proj == 0:
                continue  # Avoid division by zero
            percent_diff = ((actual - proj) / proj) * 100
            total_percent_diff += percent_diff

            if actual > proj:
                total_overperf_percent_diff += percent_diff
                overperf_count += 1
            elif actual < proj:
                total_underperf_percent_diff += percent_diff
                underperf_count += 1

        total_players = len(chosen_lineup)
        metrics['average_percent_difference'] = total_percent_diff / total_players if total_players else 0
        metrics['average_overperf_percent_diff'] = total_overperf_percent_diff / overperf_count if overperf_count else 0
        metrics['average_underperf_percent_diff'] = total_underperf_percent_diff / underperf_count if underperf_count else 0

        # Classify player performances
        performance_categories = {'boomed': 0, 'overperformed': 0, 'underperformed': 0, 'busted': 0}

        for player in chosen_lineup:
            proj = player['projected_fantasy_points']
            actual = player['fantasy_points']
            if proj == 0:
                continue  # Avoid division by zero
            percent_diff = ((actual - proj) / proj) * 100

            if percent_diff >= 20:
                performance_categories['boomed'] += 1
            elif 0 <= percent_diff < 20:
                performance_categories['overperformed'] += 1
            elif -20 < percent_diff < 0:
                performance_categories['underperformed'] += 1
            elif percent_diff <= -20:
                performance_categories['busted'] += 1

        for key in performance_categories:
            metrics[f'percent_{key}'] = (performance_categories[key] / total_players) * 100 if total_players else 0

        # Store metrics
        team['metrics'] = metrics

    def calculate_manager_lineup_score(self):
        """
        Calculates the Manager Lineup Score for all teams after metrics have been collected.

        The Manager Lineup Score is a composite score out of 100, reflecting the manager's effectiveness.
        It combines several metrics using assigned weights to represent their importance.

        Metrics and Weights:
            - Lineup Efficiency: 40%
            - Overperformance: 20%
            - Average Percent Difference: 10%
            - Percent of Players Who Beat Projections: 10%
            - Percent Boomed: 10%
            - Percent Busted: 10% (Inverted since fewer busts are better)
        """
        # Assign weights to each metric (weights should sum to 1)
        weights = {
            'lineup_efficiency': 0.4,
            'overperformance': 0.2,
            'average_percent_difference': 0.1,
            'percent_players_beat_projection': 0.1,
            'percent_boomed': 0.1,
            'percent_busted': 0.1,  # We'll subtract this from 100% in the score
        }

        # Collect max and min values needed for normalization
        max_overperformance = max([team['metrics']['overperformance'] for team in self.teams.values()], default=1)
        max_avg_percent_diff = max([team['metrics']['average_percent_difference'] for team in self.teams.values()], default=1)

        for team_id, team in self.teams.items():
            metrics = team['metrics']

            # Normalize metrics where necessary
            normalized_overperformance = (metrics['overperformance'] / max_overperformance) if max_overperformance else 0
            normalized_avg_percent_diff = (metrics['average_percent_difference'] / max_avg_percent_diff) if max_avg_percent_diff else 0

            # Calculate the Manager Lineup Score
            lineup_score = (
                (metrics['lineup_efficiency'] / 100) * weights['lineup_efficiency'] +
                normalized_overperformance * weights['overperformance'] +
                (normalized_avg_percent_diff / 100) * weights['average_percent_difference'] +
                (metrics['percent_players_beat_projection'] / 100) * weights['percent_players_beat_projection'] +
                (metrics['percent_boomed'] / 100) * weights['percent_boomed'] +
                ((100 - metrics['percent_busted']) / 100) * weights['percent_busted']  # Since fewer busts is better
            ) * 100  # Scale to 0-100

            metrics['manager_lineup_score'] = lineup_score

    def analyze(self):
        """
        Runs the analysis for all teams.
        """
        # First, calculate team metrics to get values needed for normalization
        for team_id in self.teams:
            self.calculate_optimal_lineup(team_id, use_projection=True)
            self.calculate_optimal_lineup(team_id, use_projection=False)
            self.calculate_actual_lineup(team_id)
            self.calculate_team_metrics(team_id)

        # Now that we have all metrics, calculate the Manager Lineup Score
        self.calculate_manager_lineup_score()

    def rank_teams(self):
        """
        Ranks teams based on their metrics.

        Returns:
            dict: Rankings for each metric.
        """
        # Extract metrics for all teams
        metrics = {}
        for team_id, team in self.teams.items():
            metrics[team_id] = team['metrics']

        # Rankings for each metric
        rankings = {
            'lineup_efficiency': [],
            'overperformance': [],
            'average_percent_difference': [],
            'percent_players_beat_projection': [],
            'manager_lineup_score': [],
            'chosen_vs_optimal_actual': [],  # Include if not already present
        }

        # Lineup efficiency ranking
        lineup_efficiency = sorted(metrics.items(), key=lambda x: x[1]['lineup_efficiency'], reverse=True)
        rankings['lineup_efficiency'] = [(self.teams[team_id]['team_name'], metric['lineup_efficiency']) for
                                         team_id, metric in lineup_efficiency]

        # Overperformance ranking
        overperformance = sorted(metrics.items(), key=lambda x: x[1]['overperformance'], reverse=True)
        rankings['overperformance'] = [(self.teams[team_id]['team_name'], metric['overperformance']) for team_id, metric
                                       in overperformance]

        # Average percent difference ranking
        avg_percent_diff = sorted(metrics.items(), key=lambda x: x[1]['average_percent_difference'], reverse=True)
        rankings['average_percent_difference'] = [
            (self.teams[team_id]['team_name'], metric['average_percent_difference']) for team_id, metric in
            avg_percent_diff]

        # Percent players beat projection
        percent_players_beat_projection = sorted(metrics.items(), key=lambda x: x[1]['percent_players_beat_projection'],
                                                 reverse=True)
        rankings['percent_players_beat_projection'] = [
            (self.teams[team_id]['team_name'], metric['percent_players_beat_projection']) for team_id, metric in
            percent_players_beat_projection]

        # Manager Lineup Score ranking
        manager_lineup_score = sorted(metrics.items(), key=lambda x: x[1]['manager_lineup_score'], reverse=True)
        rankings['manager_lineup_score'] = [(self.teams[team_id]['team_name'], metric['manager_lineup_score']) for
                                            team_id, metric in manager_lineup_score]

        # Points Left on Bench ranking (chosen_vs_optimal_actual)
        chosen_vs_optimal_actual = sorted(metrics.items(), key=lambda x: x[1]['chosen_vs_optimal_actual'])
        rankings['chosen_vs_optimal_actual'] = [(self.teams[team_id]['team_name'], metric['chosen_vs_optimal_actual'])
                                                for team_id, metric in chosen_vs_optimal_actual]

        return rankings

    def print_rankings(self, rankings):
        """
        Prints the rankings in a readable format with descriptions.

        Args:
            rankings (dict): The rankings to print.
        """
        metric_descriptions = {
            'lineup_efficiency': (
                "Lineup Efficiency (Chosen Points / Optimal Actual Points):\n"
                "This metric measures how close the manager's chosen lineup was to the optimal actual lineup.\n"
                "A higher percentage indicates better lineup decisions. Values close to 100% are ideal."
            ),
            'overperformance': (
                "Overperformance (Chosen Points - Projected Points):\n"
                "This metric indicates how much the chosen lineup exceeded projections.\n"
                "Positive values suggest the team performed better than expected, possibly due to good luck or astute picks.\n"
                "Negative values indicate underperformance."
            ),
            'average_percent_difference': (
                "Average Percent Difference Between Actual and Projected Points:\n"
                "This metric calculates the average percentage by which players in the chosen lineup overperformed or underperformed their projections.\n"
                "Higher positive values indicate greater overall overperformance."
            ),
            'percent_players_beat_projection': (
                "Percentage of Players Who Beat Projections:\n"
                "This metric shows the percentage of players in the chosen lineup who scored more than their projected points.\n"
                "Higher percentages indicate better overall player performance."
            ),
            'manager_lineup_score': (
                "Manager Lineup Score (Out of 100):\n"
                "This comprehensive score evaluates the manager's effectiveness in setting their lineup.\n"
                "It aggregates various metrics, including lineup efficiency, overperformance, and player performance categories.\n"
                "Higher scores indicate better managerial decisions."
            ),
            'chosen_vs_optimal_actual': (
                "Points Left on Bench (Optimal Actual Points - Chosen Points):\n"
                "This metric represents the difference between the optimal actual lineup's points and the chosen lineup's points.\n"
                "Lower values are better, suggesting that the manager made lineup decisions close to the optimal."
            ),
        }

        print("Rankings:\n")
        for metric, ranking in rankings.items():
            print(f"--- {metric.replace('_', ' ').title()} ---")
            print(metric_descriptions[metric])
            print("\nRankings:")
            for rank, (team_name, value) in enumerate(ranking, 1):
                # Interpret the value based on the metric
                if metric in ['lineup_efficiency', 'average_percent_difference', 'percent_players_beat_projection']:
                    value_str = f"{value:.2f}%"
                elif metric == 'manager_lineup_score':
                    value_str = f"{value:.2f}/100"
                else:
                    value_str = f"{value:.2f}"
                print(f"{rank}. {team_name}: {value_str}")
            print("\n")

    def run_full_analysis(self):
        """
        Runs the full analysis and prints the rankings.
        """
        self.analyze()
        rankings = self.rank_teams()
        self.print_rankings(rankings)

# Example usage
if __name__ == "__main__":
    # Load the data from the JSON file
    with open('league_data_week_1.json', 'r') as json_file:
        data = json.load(json_file)

    # Create an instance of the analyzer
    analyzer = FantasyLeagueAnalyzer(data)

    # Run the full analysis and print rankings
    analyzer.run_full_analysis()
