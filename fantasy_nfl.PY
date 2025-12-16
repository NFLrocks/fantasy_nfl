import os
from flask import Flask, request, redirect
import requests
import pandas as pd

# -----------------------------
# CONFIGURATIE
# -----------------------------
LEAGUE_ID = "49185"
CLIENT_ID = os.environ.get("YAHOO_CLIENT_ID")       # Zet dit in Render Environment
CLIENT_SECRET = os.environ.get("YAHOO_CLIENT_SECRET")  # Zet dit in Render Environment
REDIRECT_URI = os.environ.get("REDIRECT_URI")       # Bijvoorbeeld https://fantasy-nfl.onrender.com/callback

# Flask app
app = Flask(__name__)

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    # Yahoo OAuth URL
    auth_url = (
        f"https://api.login.yahoo.com/oauth2/request_auth?"
        f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Geen code ontvangen van Yahoo."

    # OAuth access token aanvragen
    token_url = "https://api.login.yahoo.com/oauth2/get_token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code != 200:
        return f"Fout bij ophalen access token: {response.text}"

    token_info = response.json()
    access_token = token_info["access_token"]

    # Data ophalen (voorbeeld: teams, standings)
    api_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{LEAGUE_ID}/standings?format=json"
    headers = {"Authorization": f"Bearer {access_token}"}
    api_response = requests.get(api_url, headers=headers)

    if api_response.status_code != 200:
        return f"Fout bij ophalen league data: {api_response.text}"

    league_data = api_response.json()

    # Data verwerken naar DataFrame
    teams = league_data["fantasy_content"]["league"][1]["standings"]["teams"]
    data_list = []
    for team_entry in teams:
        team = team_entry["team"][0]
        name = team["name"]
        wins = team["team_standings"]["outcome_totals"]["wins"]
        losses = team["team_standings"]["outcome_totals"]["losses"]
        data_list.append({"Team": name, "Wins": wins, "Losses": losses})

    df = pd.DataFrame(data_list)

    # Opslaan als Excel
    excel_file = "fantasy_league.xlsx"
    df.to_excel(excel_file, index=False)

    return f"Data opgehaald en opgeslagen in {excel_file}!"

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
