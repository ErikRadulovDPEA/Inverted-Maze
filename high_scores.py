class HighScore:
    def __init__(self):
        self.scores = {level: [] for level in range(0, 5)}

    def add_score(self, player_name, time, level):
        new_score = {'name': player_name, 'time': time}
        if not self.scores[level]:
            self.scores[level].append(new_score)
        else:
            index_to_insert = next((index for index, score in enumerate(self.scores[level]) if score['time'] > time),
                                   len(self.scores[level]))
            self.scores[level].insert(index_to_insert, new_score)

