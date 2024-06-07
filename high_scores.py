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

    def in_top_ten(self, level, time):
        if len(self.scores[level]) < 10:
            return True
        return time < self.scores[level][9]['time']

    def get_placement(self, level, time):
        for i, score in enumerate(self.scores[level]):
            if time == score['time']:
                return i+1

    def save_to_json(self):
        with open("high_scores.json", 'w') as file:
            truncated_scores = {level: self.scores[level][:3] for level in self.scores}
            json.dump(truncated_scores, file)
            # json.dump(self.scores, file)


    def load_from_json(self):
        with open("high_scores.json", 'r') as file:
            loaded_scores = json.load(file)
            self.scores = {int(level): scores for level, scores in loaded_scores.items()}
