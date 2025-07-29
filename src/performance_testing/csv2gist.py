import argparse
import pathlib
import requests
import logging
import json

# set logging
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="csv2gist.py",
        description="Push a csv file to gist",
    )
    parser.add_argument("csv", type=pathlib.Path)

    parser.add_argument("gist_id", type=str)

    parser.add_argument("--token", required=True, help="GitHub PAT to push to gist.")
    args = parser.parse_args()

    # read csv
    csv_path = args.csv
    with open(csv_path, "r") as f:
        content = f.read()

    gist = args.gist_id
    token = args.token

    gist_url = f"https://api.github.com/gists/{gist}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {"files": {"brevo-stats.csv": {"content": content}}}

    try:
        response = requests.patch(
            gist_url, data=json.dumps(payload).encode("utf-8"), headers=headers
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(e)
        logger.error(response.json())


if __name__ == "__main__":
    main()
