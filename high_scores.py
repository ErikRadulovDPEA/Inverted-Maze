import json


class HighScore:
    def __init__(self):
        self.scores = {level: [] for level in range(1, 6)}
        self.load_from_json()

    def add_score(self, player_name, time, level):
        new_score = {'name': player_name, 'time': time}
        self.scores[level].append(new_score)
        self.scores[level] = sorted(self.scores[level], key=lambda x: x['time'])
        self.save_to_json()

    def save_to_json(self):
        with open("high_scores.json", 'w') as file:
            json.dump(self.scores, file)

    def load_from_json(self):
        with open("high_scores.json", 'r') as file:
            loaded_scores = json.load(file)
            self.scores = {int(level): scores for level, scores in loaded_scores.items()}
