from flask import Flask, render_template, request, redirect, url_for, jsonify
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
    week_num = None

    if request.method == 'POST':
        # Get the week number from the form
        week_num = int(request.form['week_num'])

        # Load the data for the specified week
        data_file = f'league_data_week_{week_num}.json'
        if not os.path.exists(data_file):
            # Handle the case where the data file doesn't exist
            return f"No data available for week {week_num}. Please ensure the data file exists.", 404

        with open(data_file, 'r') as json_file:
            data = json.load(json_file)

        # Run the analysis
        analyzer = FantasyLeagueAnalyzer(data)
        analyzer.run_full_analysis()

        # Get the rankings and metrics
        rankings = analyzer.rank_teams()
        teams = analyzer.teams  # Contains all team data and metrics

        # Prepare data for rendering
        analysis_results = {
            'rankings': rankings,
            'teams': teams,
            'week_num': week_num
        }

    return render_template('analysis.html', analysis=analysis_results)


if __name__ == '__main__':
    app.run(debug=True)
