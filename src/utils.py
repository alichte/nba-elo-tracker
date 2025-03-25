import pandas as pd

class Team:
    def __init__(self, name: str, initial_elo=1500):
        self.name = name
        self.elo_history = [{"date": None, "elo": initial_elo}]

    def get_latest_elo(self):
        return self.elo_history[-1]["elo"]

    def update_elo(self, new_elo, date):
        self.elo_history.append({"date": date, "elo": new_elo})


class EloTracker:
    def __init__(self, k_factor=20):
        self.teams = {}
        self.k_factor = k_factor

    def add_team(self, name: str):
        self.teams[name] = Team(name)

    def record_game(self, home_team: str, away_team: str, home_score: int, away_score: int, date: str):
        home_team_elo = self.teams[home_team]
        away_team_elo = self.teams[away_team]

        home_elo = home_team_elo.get_latest_elo()
        away_elo = away_team_elo.get_latest_elo()

        # Apply home court advantage
        home_elo += 100 # This is the amount FiveThirtyEight used

        # Calculate actual scores
        spread = home_score - away_score 

        # Find margin multiplier
        # If favorite won, elo_diff is positive, if underdog, elo_diff is negative 
        home_favored = 1 if home_elo >= away_elo else -1
        home_won = 1 if spread > 0 else -1 
        elo_diff_raw = home_elo - away_elo
        elo_diff_m = home_won * home_favored
        elo_diff = elo_diff_raw * elo_diff_m
        MOV_m = ((abs(spread) + 3) ** 0.8) / (7.5 + 0.006*elo_diff)


        home_actual = 1 if home_score > away_score else 0 if home_score < away_score else 0.5
        away_actual = 1 - home_actual
        # divide by 28 for point expected 
        # Calculate expected win probability 
        home_expected = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        away_expected = 1 / (1 + 10 ** ((home_elo - away_elo) / 400))

        # Update Elo ratings
        new_home_elo = round((home_elo - 100) + self.k_factor * MOV_m * (home_actual - home_expected))
        new_away_elo = round(away_elo + self.k_factor * MOV_m * (away_actual - away_expected))

        # Append new Elo ratings
        home_team_elo.update_elo(new_home_elo, date)
        away_team_elo.update_elo(new_away_elo, date)

    def get_team_elo_history(self, team: str):
        return self.teams[team].elo_history
    
    def get_results_df(self):
        rows = []
        for team_name, team_elo in self.teams.items():
            for history_entry in team_elo.elo_history:
                rows.append((team_name, history_entry["date"], history_entry["elo"]))

        df = pd.DataFrame(rows, columns = ['team', 'date', 'elo'])
        return df


# Process game results
def process_game_results(elo_tracker, game_results):

    played_games = [game for game in game_results if game['home_team_score']]
    # Process each game result
    for game in played_games:
        elo_tracker.record_game(
            home_team=game['home_team'].value,
            away_team=game['away_team'].value,
            home_score=game['home_team_score'],
            away_score=game['away_team_score'],
            date=game['start_time'].strftime('%Y-%m-%d')
        )

    # Return the updated tracker
    return elo_tracker


