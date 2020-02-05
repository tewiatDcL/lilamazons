# An object representing a single match of lil'Amazons.

class Match:
    def __init__(self, match_id):
        self.id = match_id
        print(f'Match#{self.id} initialized')
