import pickle
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import re

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

def clean_team_name(name):
    # Remove non-ASCII characters from the team name
    cleaned_name = re.sub(r'[^\x00-\x7F]+', '', name)
    return cleaned_name

class YahooFantasyAPI:
    def __init__(self):
        """
        Initializes the YahooFantasyAPI class, setting up the Chrome WebDriver with the required options.
        """
        # Set up Chrome options (e.g., to run in headless mode, you can add chrome_options.add_argument("--headless"))
        chrome_options = Options()

        # Initialize the WebDriver using ChromeDriverManager to automatically manage ChromeDriver binary
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Navigate to Yahoo Fantasy Football login page
        self.driver.get("https://football.fantasysports.yahoo.com/")

        # Load previously saved cookies to maintain session
        self.load_cookies()

    def load_cookies(self):
        """
        Loads cookies from a pickle file to maintain the session across requests.
        """
        # Load cookies from the file 'yahoo_cookies.pkl'
        with open("archive/yahoo_cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                cookie['domain'] = ".yahoo.com"  # Ensure cookies are set for the correct domain
                try:
                    self.driver.add_cookie(cookie)  # Add the cookie to the browser
                except Exception as e:
                    print(f"Failed to add cookie {cookie}: {e}")

        # Refresh the page after adding cookies to ensure they take effect
        self.driver.refresh()

    def get_team_roster_by_week(self, league_id, team_id, week_num):
        """
        Fetches the roster of a specific team for a given week.

        Args:
            league_id (str): The ID of the Yahoo Fantasy Football league.
            team_id (int): The ID of the team within the league.
            week_num (int): The week number for which to fetch the roster.

        Returns:
            list: A list of player data dictionaries.
        """
        # Construct the URL for the team's roster page for the specific week
        url = f"https://football.fantasysports.yahoo.com/f1/{league_id}/{team_id}/team?&week={week_num}&stat1=S&stat2=W"
        self.driver.get(url)

        # Wait for the page to fully load
        self.driver.implicitly_wait(5)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Get the team name from the page header
        team_name_tag = soup.find('span', class_='Navtarget F-reset No-case Fz-35 Fw-b team-name')
        # Inside the `get_team_roster_by_week` method
        team_name = clean_team_name(team_name_tag.get_text(strip=True)) if team_name_tag else f'Team {team_id}'

        # Initialize list to aggregate all player data
        all_players = []

        # Loop through the tables containing player stats
        for table_id in ['statTable0', 'statTable1', 'statTable2']:
            stat_table = soup.find('table', id=table_id)
            if stat_table:
                # Parse the player data from the table
                players = self.parse_player_data(str(stat_table), team_name)
                all_players.extend(players)  # Add the players to the aggregate list
            else:
                print(f"Table with id '{table_id}' not found.")

        return all_players

    def parse_player_data(self, table_html, team_name):
        """
        Parses player data from the given HTML table.

        Args:
            table_html (str): The HTML content of the table to parse.
            team_name (str): The name of the team to associate with each player.

        Returns:
            list: A list of dictionaries containing player data.
        """
        soup = BeautifulSoup(table_html, 'html.parser')

        # Find the table body containing player rows
        tbody = soup.find('tbody')

        # List to hold parsed player data
        players = []

        if tbody:
            # Iterate through each row in the table body
            for row in tbody.find_all('tr'):
                player_data = {}

                # Extract the player's position
                position_td = row.find('td', class_='pos')
                if position_td:
                    player_data['lineup_pos'] = position_td.get_text(strip=True)

                # Extract player name and team information
                player_td = row.find('td', class_='player')
                if player_td:
                    name_tag = player_td.find('a', class_='name')
                    if name_tag:
                        player_data['name'] = name_tag.get_text(strip=True)
                    team_pos_info = player_td.find('span', class_='Fz-xxs')
                    if team_pos_info:
                        team_pos_info_text = team_pos_info.get_text(strip=True)
                        player_data['team'] = team_pos_info_text.split(' - ')[0]
                        player_data['position'] = team_pos_info_text.split(' - ')[1]

                # Extract game status (e.g., if the player is injured or suspended)
                status_td = row.find('td', class_='player-status')
                if status_td:
                    status_info = status_td.find('span', class_='ysf-game-status')
                    if status_info:
                        player_data['status'] = status_info.get_text(strip=True)

                # Extract bye week information (if applicable)
                bye_week_div = row.find('td', class_='Alt Ta-end Bdrstart')
                if bye_week_div:
                    player_data['bye_week'] = bye_week_div.get_text(strip=True)

                # Extract the fantasy points scored that week
                points_td = row.find('td', class_='Ta-end Nowrap pts Bdrstart')
                player_data['fantasy_points'] = safe_float_conversion(
                    points_td.get_text(strip=True)) if points_td else 0.0

                # Extract projected fantasy points for the week
                projected_pts_div = row.find('div', class_='F-shade Fw-b')
                if not projected_pts_div:
                    projected_pts_div = row.find('div', class_='F-shade')

                # Attempt to find projected points in the <td> with the class 'Alt Ta-end Nowrap'
                if not projected_pts_div:
                    projected_pts_div = row.find('td', class_='Alt Ta-end Nowrap')

                player_data['projected_fantasy_points'] = safe_float_conversion(
                    projected_pts_div.get_text(strip=True)) if projected_pts_div else 0.0

                # Calculate points difference
                player_data['points_diff'] = player_data['fantasy_points'] - player_data['projected_fantasy_points']

                # Add team name to the player data
                player_data['team_name'] = team_name

                # Only add player data if essential fields are not empty
                if all(player_data.get(key) for key in ['name', 'team', 'position', 'bye_week']):
                    players.append(player_data)

        return players

    def get_league_data_by_week(self, league_id, week_num, team_count=12):
        """
        Fetches the data for all teams in the league for a given week.

        Args:
            league_id (str): The ID of the Yahoo Fantasy Football league.
            week_num (int): The week number for which to fetch the data.
            team_count (int): The number of teams in the league (default is 12).

        Returns:
            dict: A dictionary where the keys are team IDs and values are lists of player data.
        """
        league_data = {}

        for team_id in range(1, team_count + 1):
            # Fetch the roster for each team
            team_roster = self.get_team_roster_by_week(league_id, team_id, week_num)
            league_data[team_id] = team_roster
            time.sleep(5)  # Delay between requests to avoid overwhelming the server

        return league_data

    def close(self):
        """
        Closes the WebDriver instance, shutting down the browser.
        """
        self.driver.quit()


# Example usage for testing the YahooFantasyAPI class
if __name__ == "__main__":
    yahoo_api = YahooFantasyAPI()
    league_id = "22030"  # Example league ID
    week_num = 1  # Week number to fetch

    # Fetch the league data for the specified week
    league_data = yahoo_api.get_league_data_by_week(league_id, week_num)
    print(league_data)

    # Save the league data to a JSON file
    filename = f'league_data_week_{week_num}.json'
    with open(filename, 'w') as json_file:
        json.dump(league_data, json_file, indent=4)

    print(f"League data for week {week_num} saved to {filename}")

    # Print the league data for each team
    for team_id, roster in league_data.items():
        print(f"Team {team_id}:")
        for player in roster:
            print(player)
        print("\n")

    # Close the browser instance
    yahoo_api.close()
