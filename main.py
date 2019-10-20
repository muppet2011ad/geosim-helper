import praw, re, datetime, groups
from claim import Claim

reddit = praw.Reddit("bot1") # Loads the config from praw.ini

geosim = reddit.subreddit("geosim") # Gets us a subreddit instance for /r/geosim

organisations = groups.getOrgs()

class PingUse(object):
    def __init__(self, player, time):
        self.player = player
        self.time = time

def getClaims():
    playermasterlist = geosim.wiki["players"].content_md # Fetches the content of the player master list

    claimslist = [] # Creates a list to store all of our claims
    countries = []

    for line in playermasterlist.split("\n"): # For every line of text in the player master list
        if line[0] != "[" or "/u/" not in line.split("|")[1]: # If it's not a line about a claim
            continue # Ignore it
        country = re.search(r"\[(.*?)\]",line).group().replace("[","").replace("]","") # Regex to identify the country in square brackets
        player = re.search(r"\/u\/[^|\* ]*",line.split("|")[1]).group() # Regex to extract the player from the line
        claimslist.append(Claim(country,player)) # Creates a new claim object
        countries.append(country)
        claimslist = sorted(claimslist, key = lambda claim: claim.country)
        countries = sorted(countries, key =  lambda country: country)
    
    return claimslist, countries

def getMods():
    moderators = geosim.moderator()
    realmods = []
    for moderator in moderators:
        if "all" in moderator.mod_permissions:
            realmods.append(moderator)
    return realmods

def handleMassPings(comment, recentuses):
    cmdregex = re.search(r"^Ping! [\w ]*", comment.body) # Regex to check for a command
    if cmdregex != None:
        try:
            comment.refresh()
        except praw.exceptions.ClientException:
            return
        commentreplies = comment.replies
        commentreplies.replace_more()
        for com in commentreplies.list(): # Ignore any comments that we've already responded to
            if com.author.name == "geosim-helper":
                return
        organisations = groups.getOrgs()
        claims, countries = getClaims() # Fetch info from geosim wiki
        if len(list(filter(lambda x: x.player.lower() == "/u/" + comment.author.name.lower(), claims))) == 0: # Catch players who aren't on the list
            print("Mass ping attempted by non-claimant:", comment.author.name)
            return
        if len(list(filter(lambda x: x.player == comment.author.name, masspinguses))) != 0: # Stop players pinging a lot
            comment.reply("You've use a mass ping too recently. Please leave 3 minutes inbetween pings.")
            return
        commentstomake = []
        grouptoping = cmdregex.group().replace("Ping! ", "") # Extract the argument of the command
        if grouptoping != "UNGA": # Everything other than UNGA
            try:
                organisation = list(filter(lambda x: x.name == grouptoping, organisations))[0] # Attempt to get the org
            except:
                comment.reply("That isn't a valid group to ping.") # Reply to the user if they try and get an invalid org
                return
        else: # If it's a UNGA ping
            nonga = list(filter(lambda x: x.name == "NonGA", organisations))[0] # Get the non-ga claims
            ungacountries = list(filter(lambda x: x not in nonga.claims, countries)) # Get the list of GA claims
            organisation = groups.Org("UNGA",ungacountries) # Create an organisation for the rest of the code to use (this is a bit of a hack)
        validpings = []
        npcs = []
        for country in organisation.claims: # For every country in the org
            if country in countries: # If they're claimed
                validpings.append(country + " - " + list(filter(lambda x: x.country == country, claims))[0].player) # Construct a ping
            else:
                npcs.append(country) # Otherwise mark them for npc
        counter = 0
        commentbody = ""
        while counter < len(validpings): # Iterate through the claims we need to ping
            commentbody = "Pinging: \n"
            for ping in validpings[counter:counter+3]:
                commentbody += "\n" + ping + "\n" # Do 3 pings at a time per reddit limitations
            counter += 3
            commentstomake.append(commentbody)
        lastcomment = comment
        for reply in commentstomake: # Create a comment chain with all of the replies
            newcom = lastcomment.reply(reply)
            lastcomment = newcom
        if len(npcs) != 0: # Add NPCs at the end if required
            npccomment = "NPCs required for: "
            for npc in npcs:
                npccomment += npc + ", "
            lastcomment.reply(npccomment[0:-2])
        masspinguses.append(PingUse(comment.author.name, datetime.datetime.now().timestamp()))

masspinguses = []

def handleModPings(comment, recentuses):
    cmdregex = re.search(r"^Mods!$", comment.body)
    if cmdregex != None:
        try:
            comment.refresh()
        except praw.exceptions.ClientException:
            return
        commentreplies = comment.replies
        commentreplies.replace_more()
        for com in commentreplies.list(): # Ignore any comments that we've already responded to
            if com.author.name == "geosim-helper":
                return
        if len(list(filter(lambda x: x.player == comment.author.name, masspinguses))) != 0: # Stop players pinging a lot
            comment.reply("You've use a mass ping too recently. Please leave 3 minutes inbetween pings.")
            return
        pings = []
        for moderator in getMods():
            pings.append("/u/" + moderator.name)
        counter = 0
        commentstomake = []
        while counter < len(pings): # Iterate through the claims we need to ping
            commentbody = "Pinging: \n"
            for ping in pings[counter:counter+3]:
                commentbody += "\n" + ping + "\n" # Do 3 pings at a time per reddit limitations
            counter += 3
            commentstomake.append(commentbody)
        lastcomment = comment
        for reply in commentstomake: # Create a comment chain with all of the replies
            newcom = lastcomment.reply(reply)
            lastcomment = newcom
        masspinguses.append(PingUse(comment.author.name, datetime.datetime.now().timestamp()))

for comment in geosim.stream.comments():
    for use in masspinguses:
        if datetime.datetime.now().timestamp() - use.time > 180:
            masspinguses.remove(use)
    handleMassPings(comment, masspinguses)
    handleModPings(comment, masspinguses)
