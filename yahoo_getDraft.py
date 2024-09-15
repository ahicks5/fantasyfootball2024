import pickle
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class YahooFantasyDraftResults:
    def __init__(self):
        """
        Initializes the YahooFantasyDraftResults class, setting up the Chrome WebDriver with the required options.
        """
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")  # Suppress logging
        chrome_options.add_argument("--disable-logging")
        # Uncomment the following line to run Chrome in headless mode
        # chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Navigate to Yahoo Fantasy Football login page
        self.driver.get("https://football.fantasysports.yahoo.com/")

        # Load previously saved cookies to maintain session
        self.load_cookies()

    def load_cookies(self):
        """
        Loads cookies from a pickle file to maintain the session across requests.
        """
        with open("archive/yahoo_cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                cookie['domain'] = ".yahoo.com"
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to add cookie {cookie}: {e}")

        # Refresh the page to ensure the session is established
        self.driver.refresh()
        time.sleep(2)  # Wait for the session to be established

    def get_draft_results(self, league_id):
        """
        Navigates to the draft results page and extracts data from the div with id 'drafttables'.

        Args:
            league_id (str): The ID of the Yahoo Fantasy Football league.
        """
        url = f"https://football.fantasysports.yahoo.com/f1/{league_id}/draftresults?drafttab=round"
        self.driver.get(url)

        # Wait for the page to load
        self.driver.implicitly_wait(5)

        # Parse the page source with BeautifulSoup
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find the div with id 'drafttables'
        draft_table_div = soup.find('div', id='drafttables')
        if not draft_table_div:
            print("No div with id 'drafttables' found.")
            return []

        draft_results = []
        round_number = 0
        pick_counter = 0

        # Loop through each tr element within the draft table div
        for tr in draft_table_div.find_all('tr'):
            # Check if the row represents a new round
            if "Round" in tr.text:
                round_number = int(tr.text.split(" ")[1])
                continue

            # Extract the pick number in the round
            pick_in_round = int(tr.find('td', class_='first').text.split('.')[0])

            # Calculate the overall pick number
            overall_pick_number = pick_in_round + (round_number - 1) * 12

            # Extract player name and player ID
            player_a_tag = tr.find('a', class_='name')
            player_name = player_a_tag.text.strip()
            player_id = player_a_tag['href'].split('/')[-1]

            # Extract player team and position
            team_position_span = tr.find('span', class_='Block')
            player_team, player_position = team_position_span.text.strip().replace('(', '').replace(')', '').split(
                ' - ')

            # Extract the drafting team name
            drafting_team_td = tr.find_all('td')[-1]
            drafting_team_name = drafting_team_td.get('title', '').strip()

            # Create the pick dictionary
            pick_info = {
                'round': round_number,
                'pick_number': overall_pick_number,
                'player_name': player_name,
                'player_id': player_id,
                'team_name': drafting_team_name,
                'player_team': player_team,
                'player_position': player_position
            }

            # Append the pick dictionary to the draft results list
            draft_results.append(pick_info)

        return draft_results

    def save_draft_results(self, draft_results, filename="draft_results.json"):
        """
        Saves the draft results to a JSON file.

        Args:
            draft_results (list): The list of draft results dictionaries.
            filename (str): The filename to save the JSON data to.
        """
        with open(filename, 'w') as json_file:
            json.dump(draft_results, json_file, indent=4)

        print(f"Draft results saved to {filename}")

    def close(self):
        """
        Closes the WebDriver instance, shutting down the browser.
        """
        self.driver.quit()


# Example usage
if __name__ == "__main__":
    yahoo_draft = YahooFantasyDraftResults()
    league_id = "22030"  # Your league ID

    # Fetch draft results
    draft_results = yahoo_draft.get_draft_results(league_id)

    print(draft_results)

    # Save the draft results to a JSON file
    yahoo_draft.save_draft_results(draft_results, "draft_results.json")

    # Close the browser instance
    yahoo_draft.close()
