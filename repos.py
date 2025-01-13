import os
import requests
import yaml
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")

if not GITHUB_TOKEN or not GITHUB_USER:
    exit(1)


def fetch_last_commit_date(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/commits"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        if commits:
            commit_date = commits[0]["commit"]["committer"]["date"]
            # Convert the date to the desired format
            date_obj = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
            return date_obj.strftime("%d-%b-%Y %H:%M")
    return "N/A"


def truncate_description(description, length=52):
    if len(description) > length:
        return description[:length] + "..."
    return description


def fetch_repo_details(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo = response.json()
        return {
            "name": repo["name"],
            "icon": "folder",  # FIXME: support arbitrary icons
            "url": repo["html_url"],
            "desc": truncate_description(repo["description"] or ""),
            "size": f"{repo['size'] / 1024:.2f}M"
            if repo["size"] >= 1024
            else f"{repo['size']}K",
            "modified": fetch_last_commit_date(repo["name"]),
        }
    return None


# load repo list
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)
    repo_names = config.get("repos", [])

repos = [
    fetch_repo_details(repo_name)
    for repo_name in repo_names
    if fetch_repo_details(repo_name)
]

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("README.md.j2")
output = template.render(github_user=GITHUB_USER, repos=repos)
with open("README.md", "w") as file:
    file.write(output)
