class Org(object):
    def __init__(self, name, claims):
        self.name = name
        self.claims = claims


def getOrgs():
	orgs = []
	with open("groups", "r") as f:
		lines = f.read().split("\n")
		print(lines)
		claimsingroup = []
		groupname = lines[0][1:]
		for line in lines [1:-1]:
			if line[0] == "-":
				orgs.append(Org(groupname, claimsingroup))
				claimsingroup = []
				groupname = line[1:]
			else:
				claimsingroup.append(line)
		orgs.append(Org(groupname, claimsingroup))
	return orgs