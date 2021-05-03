import base64
import os.path
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tqdm import tqdm

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def parse_scholar_alert_email(gmailid: str, service: build) -> list:
    """Parse scholar alert email.

    Args:
        gmailid (str): Gmail message ID.
    """
    email = service.users().messages().get(userId="me", id=gmailid).execute()
    headers = email["payload"]["headers"]
    date = ""
    subject = ""
    for h in headers:
        if h["name"] == "Date":
            date = h["value"]
        if h["name"] == "Subject":
            subject = h["value"]

    msg_str = base64.urlsafe_b64decode(
        email["payload"]["body"]["data"].encode("UTF8")
    ).decode()
    soup = BeautifulSoup(msg_str, features="html.parser")

    pt = soup.find("h3")
    papers = []
    while True:
        curr_paper = {
            "title": "",
            "authors": "",
            "snippet": "",
            "date": date,
            "subject": subject,
        }
        if pt.name == "h3":
            curr_paper["title"] = pt.text
            pt = pt.find_next_sibling()
            if (
                pt.name == "div"
                and "style" in pt.attrs
                and pt.attrs["style"] == "color:#006621"
            ):
                curr_paper["authors"] = pt.text
                pt = pt.find_next_sibling()
            if (
                pt.name == "div"
                and "class" in pt.attrs
                and pt.attrs["class"][0] == "gse_alrt_sni"
            ):
                curr_paper["snippet"] = pt.text
                pt = pt.find_next_sibling()
            if pt.name == "table":
                pt = pt.find_next_sibling()
                pt = pt.find_next_sibling()
        pt = pt.find_next_sibling()
        if curr_paper["title"] != "":
            papers.append(curr_paper)
        if not pt or curr_paper["title"] == "":
            break

    return papers


def get_gmail_service() -> build:
    """Return authenticated gmail service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build("gmail", "v1", credentials=creds)
    return service


def get_scholar_alerts_as_df() -> pd.DataFrame:
    """Return scholar alerts as dataframe."""
    service = get_gmail_service()

    # Get emails from scholaralerts
    results = []
    pageToken = ""
    page = 1
    while True:
        page_results = (
            service.users()
            .messages()
            .list(
                userId="me",
                q="from:scholaralerts-noreply@google.com",
                pageToken=pageToken,
            )
            .execute()
        )
        if len(page_results["messages"]) > 0:
            results += page_results["messages"]
            print("Page {}...OK. Total emails: {}".format(page, len(results)))
        if "nextPageToken" in page_results:
            pageToken = page_results["nextPageToken"]
            page += 1
        else:
            break

    # Cache results
    Path("cache").mkdir(parents=True, exist_ok=True)

    # Parse emails
    dfs = []
    for re in tqdm(results):
        r = re["id"]
        cache_path = "cache/{}.csv".format(r)
        if os.path.exists(cache_path):
            dfs.append(pd.read_csv(cache_path))
            continue
        alert_df = pd.DataFrame.from_records(
            parse_scholar_alert_email(r, service),
            columns=["title", "authors", "snippet", "date", "subject"],
        )
        alert_df.to_csv(cache_path, index=0)
        dfs.append(alert_df)

    # Join and sort dataframes
    dfs = pd.concat(dfs)
    dfs["date"] = pd.to_datetime(dfs["date"])
    dfs.sort_values("date", ascending=0)
    return dfs
    dfs = (
        dfs.sort_values("date")
        .groupby(["title", "authors", "snippet"])
        .apply(lambda x: [list(x["date"]), list(x["subject"])])
        .apply(pd.Series)
        .reset_index()
    )
    dfs = dfs.rename(columns={0: "date", 1: "subject"})
    return dfs


scholar_alerts_df = get_scholar_alerts_as_df()

# Generate table html
html_string = """
<html>
  <link rel="stylesheet" type="text/css" href="{stylecss}"/>
  <body>
    <div class="container">
        <div class="fixed">
            <span style="font-size:30pt">Papers</span>
            {table}
        </div>
    </div>
  </body>
</html>.
"""

# OUTPUT AN HTML FILE
with open("table.html", "w") as f:
    f.write(
        html_string.format(
            stylecss="df_style.css", table=scholar_alerts_df.to_html(classes="mystyle"),
        )
    )
