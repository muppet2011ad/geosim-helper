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
    comment.refresh()
    commentreplies = comment.replies
    commentreplies.replace_more()
    for com in commentreplies.list():
        if com.author.name == "geosim-helper":
            return
    cmdregex = re.search(r"^Ping! [\w ]*", comment.body)
    if cmdregex != None:
        claims, countries = getClaims()
        if len(list(filter(lambda x: x.player == "/u/" + comment.author.name, claims))) == 0:
            print("Mass ping attempted by non-claimant:", comment.author.name)
            return
        commentstomake = []
        grouptoping = cmdregex.group().replace("Ping! ", "")
        if grouptoping != "UNGA":
            try:
                organisation = list(filter(lambda x: x.name == grouptoping, organisations))[0]
            except:
                comment.reply("That isn't a valid group to ping.")
                return
        else:
            nonga = list(filter(lambda x: x.name == "NonGA", organisations))[0]
            ungacountries = list(filter(lambda x: x not in nonga.claims, countries))
            organisation = groups.Org("UNGA",ungacountries)
        validpings = []
        npcs = []
        for country in organisation.claims:
            if country in countries:
                validpings.append(country + " - " + list(filter(lambda x: x.country == country, claims))[0].player)
            else:
                npcs.append(country)
        counter = 0
        commentbody = ""
        while counter < len(validpings):
            commentbody = "Pinging: \n"
            for ping in validpings[counter:counter+3]:
                commentbody += "\n" + ping + "dfgndfgjkn\n"
            counter += 3
            commentstomake.append(commentbody)
        lastcomment = comment
        for reply in commentstomake:
            newcom = lastcomment.reply(reply)
            lastcomment = newcom
        if len(npcs) != 0:
            npccomment = "NPCs required for: "
            for npc in npcs:
                npccomment += npc + ", "
            lastcomment.reply(npccomment[0:-2])

for comment in geosim.stream.comments():
    handleMassPings(comment)