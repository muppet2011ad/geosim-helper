class Claim(object): # Container class for information about a claim
    def __init__(self, country="undefined",player="undefined",last=0):
        self.country = country
        self.player = player
        self.last = last