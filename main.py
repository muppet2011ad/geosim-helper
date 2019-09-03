import praw, re, datetime, groups

from claim import Claim

reddit = praw.Reddit("bot1") # Loads the config from praw.ini

geosim = reddit.subreddit("geosim") # Gets us a subreddit instance for /r/geosim

organisations = groups.getOrgs()

def getClaims():
    playermasterlist = geosim.wiki["players"].content_md # Fetches the content of the player master list

    claimslist = [] # Creates a list to store all of our claims
    countries = []

    for line in playermasterlist.split("\n"): # For every line of text in the player master list
        if line[0] != "[" or "/u/" not in line: # If it's not a line about a claim
            continue # Ignore it
        country = re.search(r"\[(.*?)\]",line).group().replace("[","").replace("]","") # Regex to identify the country in square brackets
        player = re.search(r"\/u\/[^|\* ]*",line).group() # Regex to extract the player from the line
        claimslist.append(Claim(country,player)) # Creates a new claim object
        countries.append(country)
        claimslist = sorted(claimslist, key = lambda claim: claim.country)
        countries = sorted(countries, key =  lambda country: country)
    
    return claimslist, countries

def handleMassPings(comment):
    cmdregex = re.search(comment.body, r"Ping! [\w]*")
    if cmdregex != None:
        commentstomake = []
        grouptoping = cmdregex.group().replace("Ping! ", "")
        try:
            organisation = list(filter(lambda x: x.name == grouptoping, organisations))[0]
        except:
            comment.reply("That isn't a valid group to ping.")
            return
        validpings = []
        for claim in organisation.claims:
            if claim in countries:
                validpings.append(claim.country + " - " + claim.player)
        print(validpings)
        

claims, countries = getClaims()

handleMassPings("Ping! UNSC")

for comment in geosim.stream.comments(skip_existing=True):
    pass