# fantasy_nfl.py
from flask import Flask, request
import webbrowser
import requests
import pandas as pd
import threading
import time

# -----------------------------
# VUL HIER JE APP GEGEVENS IN
CLIENT_ID = '49185'
CLIENT_SECRET = '4ead520ed7e5af90a0741046c64c8cd03d974b90'  
REDIRECT_URI = 'https://defeatedly-discalced-lavone.ngrok-free.dev/callback' # Exact zoals in je Yahoo-app

app = Flask(__name__)
auth_code = None

# -----------------------------
# Open browser voor Yahoo login
auth_url = f"https://api.login.yahoo.com/oauth2/request_auth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&language=en-us"
print("De browser wordt geopend voor Yahoo login...")
webbrowser.open(auth_url)

# -----------------------------
# Callback route
@app.route('/callback')
def callback():
    global auth_code
    auth_code = request.args.get('code')
    return "OAuth code ontvangen! Sluit deze browser en ga terug naar het script."

# -----------------------------
# Start Flask in een aparte thread
def run_flask():
    app.run(port=8080)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Wacht tot de code is ontvangen
while auth_code is None:
    time.sleep(1)

# -----------------------------
# Haal access token op
token_url = "https://api.login.yahoo.com/oauth2/get_token"
data = {
    'grant_type': 'authorization_code',
    'code': auth_code,
    'redirect_uri': REDIRECT_URI,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET
}
response = requests.post(token_url, data=data)
tokens = response.json()
access_token = tokens['access_token']
print("Access token ontvangen!")

# -----------------------------
# Haal League IDs op
headers = {"Authorization": f"Bearer {access_token}"}
url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nfl/leagues?format=json"
response = requests.get(url, headers=headers)
data = response.json()

league_ids = {}
leagues = data['fantasy_content']['users'][0]['user'][1]['games']['0']['game'][1]['leagues']
for league in leagues:
    season = league['league'][0]['season']
    league_key = league['league'][0]['league_key']
    if int(season) >= 2012:
        league_ids[int(season)] = league_key

print("League IDs per seizoen:", league_ids)

# -----------------------------
# Data ophalen en Excel maken
all_seasons_data = []

for year, league_key in sorted(league_ids.items()):
    print(f"Ophalen van seizoen {year}...")
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/standings?format=json"
    response = requests.get(url, headers=headers)
    data = response.json()
    
    teams = data['fantasy_content']['league'][1]['standings']['0']['teams']
    for team in teams:
        t = team['team'][0]
        all_seasons_data.append({
            "Seizoen": year,
            "Team": t['name'],
            "Manager": t['managers'][0]['nickname'],
            "Points": t['team_points']['total']['points'],
            "Wins": t['team_stats']['outcome_totals']['wins'],
            "Losses": t['team_stats']['outcome_totals']['losses'],
            "Ties": t['team_stats']['outcome_totals']['ties']
        })

df = pd.DataFrame(all_seasons_data)
excel_filename = "FantasyNFL_2012_heden.xlsx"
df.to_excel(excel_filename, index=False)
print(f"Excel-bestand aangemaakt: {excel_filename}")
