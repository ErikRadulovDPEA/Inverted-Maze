class HighScore:
    def __init__(self): #i should add the different highscore boards to this rather than making whole enw screen
        self.scores = []

    def add_score(self, player_name, time):
        new_score = {'name': player_name, 'time': time}
        if not self.scores:
            self.scores.append(new_score)
        else:
            index_to_insert = next((index for index, score in enumerate(self.scores) if score['time'] > time), len(self.scores))
            self.scores.insert(index_to_insert, new_score)

