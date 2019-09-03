import praw, re, datetime

from claim import Claim

reddit = praw.Reddit("bot1") # Loads the config from praw.ini

geosim = reddit.subreddit("geosim") # Gets us a subreddit instance for /r/geosim

def getClaims():
    playermasterlist = geosim.wiki["players"].content_md # Fetches the content of the player master list

    claimslist = [] # Creates a list to store all of our claims

    for line in playermasterlist.split("\n"): # For every line of text in the player master list
        if line[0] != "[" or "/u/" not in line: # If it's not a line about a claim
            continue # Ignore it
        country = re.search(r"\[(.*?)\]",line).group().replace("[","").replace("]","") # Regex to identify the country in square brackets
        player = re.search(r"\/u\/[^|\* ]*",line).group() # Regex to extract the player from the line
        claimslist.append(Claim(country,player)) # Creates a new claim object
        claimslist = sorted(claimslist, key = lambda claim: claim.country)
    
    return claimslist

