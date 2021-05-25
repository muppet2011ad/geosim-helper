from claim import Claim, getClaims
import praw, re, datetime, groups, os, math, sys, atexit

logfile = ""

def log(text):
    global logfile
    logfile += text + "\n\n"
    print(text)

def exit_handler():
    global logfile
    global geosim
    geosim.wiki["vault/log"].edit(logfile, "Update logfile on exit")

atexit.register(exit_handler)

class CountryPosts(object):
    def __init__(self):
        self.map = {}
    def add_post(self, country, post):
        if country in self.map:
            self.map[country].append(post)
        else:
            self.map[country] = [post]

def date_irl_to_ig(dateirl, season_start):
    season_start = datetime.datetime.fromisoformat(season_start)
    year = str(math.floor((dateirl - season_start.timestamp())/604800) + season_start.year)
    lookup = ["February/March", "April/May", "June", "July/August", "September/October", "November/December", "January"]
    month = lookup[datetime.datetime.fromtimestamp(dateirl, tz=datetime.timezone.utc).weekday()]
    return month + " " + year

reddit = praw.Reddit(
    client_id=os.getenv("client_id"),
    client_secret=os.getenv("client_secret"),
    password=os.getenv("password"),
    user_agent="Geosim Archiver 1.0",
    username=os.getenv("username")
) 

geosim = reddit.subreddit("geosim") # Gets us a subreddit instance for /r/geosim

log("Connected to /r/geosim")

if geosim.wiki["vault/command"].content_md:
    if geosim.wiki["vault/command"].content_md == "reset":
        log("Detected reset command, clearing all /vault pages")
        pages_to_clear = [page for page in geosim.wiki if page.name[:6] == "vault/" and page.name not in ["vault/seasonstart", "vault/lastrun", "vault/log"]]
        for page in pages_to_clear:
            page.edit("", "Reset command for geosim-helper")
        geosim.wiki["vault/lastrun"].edit(str(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()), "Update complete")
        sys.exit()

claims, countries = getClaims(geosim, merge2ic=True) # Parse claims from the PML
log("Found " + str(len(claims)) + " claims")

lastrun_timestamp = float(geosim.wiki["vault/lastrun"].content_md) # Gets last run timestamp from geosim

newposts = geosim.new() # Looks at new posts

country_to_posts = CountryPosts()

log("Organising posts by country...")

def handle_post(post, country_to_posts):
    if "[meta]" in post.title.lower():
        country_to_posts.add_post("Meta", post)
    elif "[modpost]" in post.title.lower():
        country_to_posts.add_post("Modpost", post)
    elif "[modevent]" in post.title.lower() or "[minimodevent]" in post.title.lower():
        country_to_posts.add_post("Modevent", post)
    elif "[battle]" in post.title.lower():
        country_to_posts.add_post("Battle", post)
    elif "[un]" in post.title.lower():
        country_to_posts.add_post("UN", post)
    elif "[map]" in post.title.lower():
        country_to_posts.add_post("Map", post)
    elif "[claim]" in post.title.lower() or post.link_flair_text == "Claim" or "[date]" in post.title.lower():
        pass
    else:
        country = "deferred"
        for claim in claims:
            if claim.player.lower() == "/u/" + post.author.name.lower():
                country = claim.country
                break
        country_to_posts.add_post(country, post)

search_time = str(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()-180)

old_urls = geosim.wiki["vault/lasturls"].content_md.split("\n")

for post in newposts: # Iterate through posts
    if post.created_utc > lastrun_timestamp and post.permalink not in old_urls: # If post is more recent than our last timestamp
        handle_post(post, country_to_posts)
    else:
        break

deferred_pages = [line for line in geosim.wiki["vault/deferred"].content_md.split("\n") if line[:3] == "/r/"] # Get a list of deferred pages
for link in deferred_pages: # For every link
    post = praw.models.Submission(reddit, url="https://reddit.com" + link) # Get the submission
    handle_post(post, country_to_posts) # And add it back to the pile to be handled

num_posts = sum([len(country_to_posts.map[country]) for country in country_to_posts.map])

log(str(num_posts) + " posts organised, of which " + str(len(country_to_posts.map["deferred"])) + " will be deferred.")

index = geosim.wiki["vault/index"]

log("Maintaining index page...")

# Maintain the index page as required
try:
    content = index.content_md # Try and access the content
except: # If we have an issue, we need to make the wiki page in the first place
    index.edit("", "Create page")
    content = ""
finally:
    if content != "":
        content_meta, content_country = content.split("---")
        lines_meta = [line for line in content_meta.split("\n") if line and line[0] != "#"]
        lines_country = [line for line in content_country.split("\n") if line and line[0] != "#"]
        reason = "Index update" # Extract existing index content if it already exists
    else:
        lines_meta = []
        lines_country = []
        reason = "Create index" # Otherwise start from scratch

    # Creates a bullet point for every meta group
    meta_groups = {group:posts for (group, posts) in country_to_posts.map.items() if group in ["Meta", "Modpost", "Modevent", "Battle", "UN", "Map"] and group not in content}
    for group in meta_groups.keys():
        lines_meta.append("* [{group}] ({link})".format(group=group, link="https://reddit.com/r/geosim/wiki/vault/" + group.lower().replace(" ", "")))

    # Creates a bullet point for every country
    country_groups = {group:posts for (group, posts) in country_to_posts.map.items() if group not in ["Meta", "Modpost", "Modevent", "Battle", "deferred", "UN", "Map"] and group not in content}
    for group in country_groups.keys():
        lines_country.append("* [{group}] ({link})".format(group=group, link="https://reddit.com/r/geosim/wiki/vault/" + group.lower().replace(" ", "")))

    new_content = "##Meta posts and Mod actions\n" + "\n".join(sorted(lines_meta)) + "\n\n---\n\n##Countries\n" + "\n".join(sorted(lines_country))
    index.edit(new_content, reason)

log("Index complete")
        
season_start = geosim.wiki["vault/seasonstart"].content_md
flair_re = re.compile(r"\[[\w]+\]")
urls = []

# Now we need to maintain the page for every single country
for country in country_to_posts.map:
    log("Handling " + country + "...")
    if country != "deferred":
        page = geosim.wiki["vault/" + country.lower().replace(" ", "")]
        rows = []
        try:
            content = page.content_md
            rows = [line for line in content.split("\n")[3:]]
        except:
            page.edit("", "Create page")
        finally:
            content = "##{country} Posts\nType | Title | Author | In-game Date | Date IRL\n---|---|---|---|---\n".format(country=country)
            new_rows = []
            for post in country_to_posts.map[country]:
                flair_search = re.match(flair_re, post.title)
                try:
                    flair = post.title[flair_search.start():flair_search.end()].replace("[", "").replace("]", "")
                    post_title = re.split(flair_re, post.title)[1]
                except:
                    flair = ""
                    post_title = post.title
                if post_title and post_title[0] == " ":
                    post_title = post_title[1:]
                author = "/u/" + post.author.name
                date_ig = date_irl_to_ig(post.created_utc, season_start)
                date_irl = datetime.datetime.fromtimestamp(post.created_utc, tz=datetime.timezone.utc).date().isoformat()
                new_rows.append("{flair} | [{title}]({link}) | {author} | {date_ig} | {date_irl}".format(flair=flair, title=post_title, link=post.permalink, author=author, date_ig=date_ig, date_irl=date_irl))
                urls.append(post.permalink)
            
            final_table_rows = new_rows + rows
            content += "\n".join(final_table_rows)
            page.edit(content, "Update page")
    else:
        page = geosim.wiki["vault/deferred"]
        content = page.content_md
        new_rows = [post.permalink for post in country_to_posts.map[country]]
        content = "\n".join(new_rows)
        page.edit(content, "Update page")
    log("Handled " + country)

geosim.wiki["vault/lasturls"].edit("\n".join(urls), "Update")

log("Done!")

geosim.wiki["vault/lastrun"].edit(search_time, "Update complete")