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
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def clean_team_name(name):
    cleaned_name = re.sub(r'[^\x00-\x7F]+', '', name)
    return cleaned_name

class YahooFantasyAPI:
    def __init__(self):
        chrome_options = Options()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.get("https://football.fantasysports.yahoo.com/")
        self.load_cookies()

    def load_cookies(self):
        with open("archive/yahoo_cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                cookie['domain'] = ".yahoo.com"
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to add cookie {cookie}: {e}")
        self.driver.refresh()

    def get_team_roster_by_week(self, league_id, team_id, week_num):
        url = f"https://football.fantasysports.yahoo.com/f1/{league_id}/{team_id}/team?&week={week_num}&stat1=S&stat2=W"
        self.driver.get(url)
        self.driver.implicitly_wait(5)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        team_name_tag = soup.find('span', class_='Navtarget F-reset No-case Fz-35 Fw-b team-name')
        team_name = clean_team_name(team_name_tag.get_text(strip=True)) if team_name_tag else f'Team {team_id}'
        all_players = []
        for table_id in ['statTable0', 'statTable1', 'statTable2']:
            stat_table = soup.find('table', id=table_id)
            if stat_table:
                players = self.parse_player_data(str(stat_table), team_name)
                all_players.extend(players)
            else:
                print(f"Table with id '{table_id}' not found.")
        return all_players

    def parse_player_data(self, table_html, team_name):
        soup = BeautifulSoup(table_html, 'html.parser')
        tbody = soup.find('tbody')
        players = []
        if tbody:
            for row in tbody.find_all('tr'):
                player_data = {}
                position_td = row.find('td', class_='pos')
                if position_td:
                    player_data['lineup_pos'] = position_td.get_text(strip=True)
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
                status_td = row.find('td', class_='player-status')
                if status_td:
                    status_info = status_td.find('span', class_='ysf-game-status')
                    if status_info:
                        player_data['status'] = status_info.get_text(strip=True)
                bye_week_div = row.find('td', class_='Alt Ta-end Bdrstart')
                if bye_week_div:
                    player_data['bye_week'] = bye_week_div.get_text(strip=True)
                points_td = row.find('td', class_='Ta-end Nowrap pts Bdrstart')
                player_data['fantasy_points'] = safe_float_conversion(points_td.get_text(strip=True)) if points_td else 0.0
                projected_pts_div = row.find('div', class_='F-shade Fw-b')
                if not projected_pts_div:
                    projected_pts_div = row.find('div', class_='F-shade')
                if not projected_pts_div:
                    projected_pts_div = row.find('td', class_='Alt Ta-end Nowrap')
                player_data['projected_fantasy_points'] = safe_float_conversion(projected_pts_div.get_text(strip=True)) if projected_pts_div else 0.0
                player_data['points_diff'] = player_data['fantasy_points'] - player_data['projected_fantasy_points']
                player_data['team_name'] = team_name
                if all(player_data.get(key) for key in ['name', 'team', 'position', 'bye_week']):
                    players.append(player_data)
        return players

    def get_league_data_by_week(self, league_id, week_num, team_count=12):
        league_data = {}
        for team_id in range(1, team_count + 1):
            team_roster = self.get_team_roster_by_week(league_id, team_id, week_num)
            league_data[team_id] = team_roster
            time.sleep(5)
        return league_data

    def close(self):
        self.driver.quit()

def save_league_data_by_week(league_data, week_num, filename):
    """Save the league data with week number as the outermost key."""
    data = {}
    try:
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        pass  # If the file doesn't exist, we'll create it

    data[week_num] = league_data

    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    yahoo_api = YahooFantasyAPI()
    league_id = "22030"
    start_week = 1
    end_week = 2
    filename = 'league_data_by_week.json'

    for week_num in range(start_week, end_week + 1):
        league_data = yahoo_api.get_league_data_by_week(league_id, week_num)
        save_league_data_by_week(league_data, week_num, filename)
        print(f"League data for week {week_num} saved to {filename}")

    yahoo_api.close()

if __name__ == "__main__":
    main()
