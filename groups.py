import praw, os

class Org(object):
	def __init__(self, name, claims):
		self.name = name
		self.claims = claims


def getOrgs():
	orgs = []
	reddit = praw.Reddit(
		client_id=os.getenv("client_id"),
		client_secret=os.getenv("client_secret"),
		password=os.getenv("password"),
		user_agent=os.getenv("user_agent"),
		username=os.getenv("username")
	) 

	geosim = reddit.subreddit("geosim")
	orgswiki = geosim.wiki["organisations"].content_md
	lines = orgswiki.split("\n")
	claimsingroup = []
	groupname = lines[0].replace("*", "").replace("\r", "").rstrip()
	for line in lines[1:-1]:
		if line.replace(" ", "").replace("\r", "") == "":
			continue
		if line[0] == "*":
			orgs.append(Org(groupname, claimsingroup))
			claimsingroup = []
			groupname = line.replace("*", "").replace("\r", "").rstrip()
		elif line[0:-1] != "":
			claimsingroup.append(line.replace("\r", "").rstrip())
	orgs.append(Org(groupname, claimsingroup))
	return orgs