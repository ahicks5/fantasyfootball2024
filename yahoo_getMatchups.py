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
        # Uncomment the following line to run Chrome in headless mode
        # chrome_options.add_argument("--headless")
        # Suppress logging
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-logging")

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
        time.sleep(2)  # Wait a bit for the session to be established

    def extract_team_id(self, url):
        """
        Extracts the team ID from the given URL.

        Args:
            url (str): The URL containing the team ID.

        Returns:
            str: The extracted team ID.
        """
        # Split the URL by '/' and get the last part
        return url.rstrip('/').split('/')[-1]

    def get_schedule_by_week(self, league_id, week_num):
        """
        Fetches the schedule (matchups) for a specific week in the league.

        Args:
            league_id (str): The ID of the Yahoo Fantasy Football league.
            week_num (int): The week number for which to fetch the schedule.

        Returns:
            list: A list of dictionaries containing matchup data.
        """
        # Construct the URL for the matchup page for the specific week
        url = f"https://football.fantasysports.yahoo.com/f1/{league_id}?matchup_week={week_num}&module=matchups&lhst=matchups"
        self.driver.get(url)

        # Wait for the page to fully load
        self.driver.implicitly_wait(5)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find the div with class 'matchups-body'
        target_div = soup.find('div', class_='matchups-body')
        if not target_div:
            print(f"No matching div with class 'matchups-body' found for week {week_num}")
            return []

        # Within this div, find the ul with class 'List'
        ul = target_div.find('ul', class_='List')
        if not ul:
            print(f"No matching ul with class 'List' found for week {week_num}")
            return []

        # Initialize list to hold matchups
        matchups = []

        # Loop through li elements
        for li in ul.find_all('li', recursive=False):
            # Find all 'a' elements with class 'F-link'
            a_tags = li.find_all('a', class_='F-link')
            if len(a_tags) >= 2:
                # Get the hrefs and extract the team IDs
                team1_href = a_tags[0]['href']
                team2_href = a_tags[1]['href']
                # Extract team IDs
                team1_id = self.extract_team_id(team1_href)
                team2_id = self.extract_team_id(team2_href)
                # Append to matchups
                matchups.append({'team1_id': team1_id, 'team2_id': team2_id})
            else:
                print(f"Not enough team links in li element for week {week_num}")
                continue

        return matchups

    def get_league_schedule(self, league_id, start_week=1, end_week=14):
        """
        Fetches the schedule for all weeks in the league.

        Args:
            league_id (str): The ID of the Yahoo Fantasy Football league.
            start_week (int): The starting week number.
            end_week (int): The ending week number.

        Returns:
            dict: A dictionary where keys are week numbers and values are lists of matchups.
        """
        schedule = {}

        for week_num in range(start_week, end_week + 1):
            print(f"Fetching schedule for week {week_num}...")
            weekly_matchups = self.get_schedule_by_week(league_id, week_num)
            schedule[week_num] = weekly_matchups
            time.sleep(2)  # Shorter delay since we're fetching less data

        return schedule

    def close(self):
        """
        Closes the WebDriver instance, shutting down the browser.
        """
        self.driver.quit()


# Example usage for testing the YahooFantasyAPI class
if __name__ == "__main__":
    yahoo_api = YahooFantasyAPI()
    league_id = "22030"  # Your league ID
    start_week = 1  # Starting week number
    end_week = 14  # Ending week number

    # Fetch the league schedule for the specified weeks
    league_schedule = yahoo_api.get_league_schedule(league_id, start_week, end_week)

    # Save the league schedule to a JSON file
    filename = f'league_schedule_weeks_{start_week}_to_{end_week}.json'
    with open(filename, 'w') as json_file:
        json.dump(league_schedule, json_file, indent=4)

    print(f"League schedule from week {start_week} to {end_week} saved to {filename}")

    # Print the league schedule for each week
    for week_num, matchups in league_schedule.items():
        print(f"Week {week_num} Matchups:")
        for matchup in matchups:
            print(f"Team {matchup['team1_id']} vs Team {matchup['team2_id']}")
        print("\n")

    # Close the browser instance
    yahoo_api.close()
