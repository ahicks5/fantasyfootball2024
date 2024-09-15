from flask import Flask, render_template, request, jsonify
import os
import json
from bestManager import FantasyLeagueAnalyzer  # Import the FantasyLeagueAnalyzer class

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    analysis_results = None
    week_num = 1  # Always show stats as of Week 1

    # Load the data from the JSON file
    data_file = 'league_data_by_week.json'
    if not os.path.exists(data_file):
        return "Data file not found. Please ensure the data file exists.", 404

    with open(data_file, 'r') as json_file:
        all_data = json.load(json_file)

    # Extract data for Week 1
    week_str = str(week_num)
    if week_str in all_data:
        combined_data = {week_str: all_data[week_str]}
    else:
        return f"No data available for week {week_num}.", 404

    # Run the analysis using the Week 1 data
    analyzer = FantasyLeagueAnalyzer(combined_data)
    analyzer.run_full_analysis()

    # Get the rankings and metrics
    rankings = analyzer.rank_teams()
    teams = analyzer.teams

    # Prepare data for rendering
    analysis_results = {
        'rankings': rankings,
        'teams': teams,
        'week_num': week_num
    }

    return render_template('analysis.html', analysis=analysis_results)


@app.route('/matchup_insights')
def matchup_insights():
    standings_file = 'standings.json'
    if not os.path.exists(standings_file):
        return "Standings file not found. Please ensure the standings file exists.", 404

    with open(standings_file, 'r') as file:
        standings = json.load(file)

    return render_template('matchup_insights.html', standings=standings)


if __name__ == '__main__':
    app.run(debug=True)
