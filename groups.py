import praw

class Org(object):
    def __init__(self, name, claims):
        self.name = name
        self.claims = claims


def getOrgs():
	orgs = []
	reddit = praw.Reddit("bot1")
	geosim = reddit.subreddit("geosim")
	orgswiki = geosim.wiki["organisations"].content_md
	lines = orgswiki.split("\n")
	claimsingroup = []
	groupname = lines[0][2:-3]
	for line in lines[1:-1]:
		if line == "\n":
			continue
		if line[0] == "*":
			orgs.append(Org(groupname, claimsingroup))
			claimsingroup = []
			groupname = line[2:-3]
		elif line[0:-1] != "":
			claimsingroup.append(line[0:-1])
	orgs.append(Org(groupname, claimsingroup))
	return orgs