import os
import json
import random
import requests


def check_issue(g, title: str) -> bool:
    """check if issue already exists upstream."""
    for issue in g.json():
        if issue.get("title") == title:
            return True
    return False


def get_base_path(g):
    """check if more pages are to be requested for upstream issues."""
    if g.headers.get("Link"):
        for next_link in g.headers.get("Link").split(","):
            if 'rel="next"' in next_link.split(";")[1]:
                return next_link.split(";")[0].strip("< >")
            return None


def get_upstream_issues(base_path: str, title: str) -> bool:
    """parse through all upstream to check for already exsisting issues."""
    while base_path:
        g = requests.get(base_path)
        if g.status_code == 200:
            base_path = get_base_path(g)
            if check_issue(g, title):
                return True
    return False


def raise_issue(url: str, issue: json) -> int:
    """raise the issue in github."""
    r = requests.post(url, json.dumps(issue))
    return r.status_code


def get_github_token():
    """fetch the required github token."""
    with open(
        os.path.join(os.path.dirname(__file__), "../plugins/tensorflow_config.json")
    ) as f:
        data = json.load(f)
    return data.get("GIT_ISSUE_API_URL"), os.getenv("SESHETA_GITHUB_ACCESS_TOKEN")


def get_expression():
    """emoji to make the issue for humanlike."""
    exp = [
        ":collision: ",
        ":exclamation: ",
        ":dizzy_face: ",
        ":scream: ",
        ":loudspeaker: ",
    ]
    return random.choice(exp)


def report_issue(entity_name, entity_status, detail="No Context"):
    """report the failure as a github issue."""
    apiurl, apitoken = get_github_token()
    url = "{}?access_token={}".format(apiurl, apitoken)
    title = "The {} has failed with status {}".format(entity_name, entity_status)
    issue = {
        "title": title,
        "body": "{} **Failed Due to:**\n **Log:**\n ```\n{}```".format(
            get_expression(), detail
        ),
        "labels": ["bug"],
    }
    issue_raised = get_upstream_issues(url, title)
    if not issue_raised:
        response_code = raise_issue(url, issue)
        if response_code == 201:
            return True
        else:
            return False
