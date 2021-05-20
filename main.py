import praw, re, datetime, groups, os
from claim import Claim

reddit = praw.Reddit(
    client_id=os.getenv("client_id"),
    client_secret=os.getenv("client_secret"),
    password=os.getenv("password"),
    user_agent=os.getenv("user_agent"),
    username=os.getenv("username")
) 

geosim = reddit.subreddit("geosim") # Gets us a subreddit instance for /r/geosim

organisations = groups.getOrgs()

# Common regexes

idcountry = re.compile(r"\[(.*?)\]")
idplayer = re.compile(r"u\/[^|\* ]*")
pingcmd = re.compile(r"^Ping! [\w ,']*")
modcmd = re.compile(r"^Mods!$")

class PingUse(object):
    def __init__(self, player, time):
        self.player = player
        self.time = time

def getClaims():
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
        player = idplayer.search(line.split("|")[1]).group() # Regex to extract the player from the line
        if player[0] != "/":
            player = "/" + player
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
    cmdregex = pingcmd.search(comment.body) # Regex to check for a command
    if cmdregex != None:
        playermasterlist = geosim.wiki["players"].content_md
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
        if len(list(filter(lambda x: x.player.lower() == "/u/" + comment.author.name.lower(), claims))) == 0 and comment.author.name.lower() != "muppet2011ad": # Catch players who aren't on the list
            print("Mass ping attempted by non-claimant:", comment.author.name)
            return
        commentstomake = []
        groupstoping = cmdregex.group().replace("Ping! ", "").split(", ") # Extract the argument of the command
        pings = []
        invalids = []
        for group in groupstoping:
            if group != "UNGA": # Everything other than UNGA
                try:
                    orgclaims = list(filter(lambda x: x.name.lower() == group.lower(), organisations))[0].claims # Attempt to get the org
                    pings += orgclaims
                except: # In this case it's not an organisation, so try looking for it on the PML
                    if group.lower() == "what":
                        comment.reply("What ain't no country I ever heard of!")
                    elif group not in playermasterlist:
                        invalids.append(group) # If it's not on the PML, they probably messed it up
                    else:
                        pings.append(group) # If it's on the PML, it's prolly a country so we'll try to ping it
            else: # If it's a UNGA ping
                nonga = list(filter(lambda x: x.name == "NonGA", organisations))[0] # Get the non-ga claims
                ungacountries = list(filter(lambda x: x not in nonga.claims, countries)) # Get the list of GA claims
                pings += ungacountries # Create an organisation for the rest of the code to use (this is a bit of a hack)
        pings = sorted(set(pings))
        organisation = groups.Org("virtualorg", pings) # This is a bit of a hack really - we merge all the claims we got into a fake organisation, which means I don't have to redo half the code for this change
        validpings = []
        npcs = []
        for country in organisation.claims: # For every country in the org
            if country in countries: # If they're claimed
                validpings.append(country + " - " + list(filter(lambda x: x.country == country, claims))[0].player) # Construct a ping
            else:
                npcs.append(country) # Otherwise mark them for npc
        if len(list(filter(lambda x: x.player == comment.author.name, masspinguses))) != 0 and len(validpings) > 6: # Stop players pinging a lot
            comment.reply("You've use a mass ping too recently. Please leave 3 minutes inbetween pings.")
            return
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
        if len(invalids) > 0:
            invalidcomment = ", ".join(invalids)
            if len(invalids) == 1:
                invalidcomment += " was not pinged as I could not find them in the [PML](http://www.reddit.com/r/geosim/wiki/players) or as an [organisation](http://www.reddit.com/r/geosim/wiki/organisations)."
            else:
                invalidcomment += " were not pinged as I could not find them in the [PML](http://www.reddit.com/r/geosim/wiki/players) or as an [organisation](http://www.reddit.com/r/geosim/wiki/organisations)."
            if len(invalidcomment) >= 10000:
                lastcomment.reply("Oi stop trying to break the bot!")
            else:
                lastcomment.reply(invalidcomment)
        if len(validpings) > 6:
            masspinguses.append(PingUse(comment.author.name, datetime.datetime.now().timestamp()))

masspinguses = []

def handleModPings(comment, recentuses):
    cmdregex = modcmd.search(comment.body)
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
            if moderator.name != "AutoModerator":
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
    if comment.author.name == "geosim-helper":
        continue
    handleMassPings(comment, masspinguses)
    handleModPings(comment, masspinguses)
