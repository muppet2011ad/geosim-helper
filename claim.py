import re

idcountry = re.compile(r"\[(.*?)\]")
idplayer = re.compile(r"u\/[^|\* ]*")

class Claim(object): # Container class for information about a claim
    def __init__(self, country="undefined",player="undefined",last=0):
        self.country = country
        self.player = player
        self.last = last

def getClaims(geosim, merge2ic=False):
    playermasterlist = geosim.wiki["players"].content_md # Fetches the content of the player master list

    claimslist = [] # Creates a list to store all of our claims
    countries = []

    for line in playermasterlist.split("\n"): # For every line of text in the player master list
        if "|" not in line or "u/" not in line.split("|")[1]: # If it's not a line about a claim
            continue # Ignore it
        if "[" in line.split("|")[0]:
            country = idcountry.search(line).group().replace("[", "").replace("]", "")  # Regex to identify the country in square brackets
        else:
            country = line.split("|")[0].lstrip().rstrip()
        if merge2ic:
            country = country.replace(" 2ic", "").replace("2ic", "")
        player = idplayer.search(line.split("|")[1]).group() # Regex to extract the player from the line
        if player[0] != "/":
            player = "/" + player
        claimslist.append(Claim(country,player)) # Creates a new claim object
        if country not in countries:
            countries.append(country)
        claimslist = sorted(claimslist, key = lambda claim: claim.country)
        countries = sorted(countries, key =  lambda country: country)
    
    return claimslist, countries