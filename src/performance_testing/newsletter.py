import requests
import argparse
import pathlib
from datetime import datetime
import logging
import os

import pandas as pd

# set logging
logger = logging.getLogger(__name__)


def get_campaign_stats(
    apikey: str,
    brevo_api_url: str = "https://api.brevo.com/v3",
    limit: int = 50,
    excludehtml: bool = True,
    csv: str = "./newsletter_stats.csv",
):
    """
    Query the entire statistics of all campaigns
    Maximum 50 campaigns will be returned and the actual
    html content of the campaign will be excluded
    """

    # http request header for authentication via API key
    headers = {"accept": "application/json", "api-key": apikey}
    campaigns_url = (
        f"{brevo_api_url}/emailCampaigns?"
        f"limit={limit}&"
        f"offset=0&sort=desc&"
        f"excludeHtmlContent={str(excludehtml).lower()}"
    )
    logger.info(f"Request stats: {campaigns_url}")
    try:
        response = requests.get(campaigns_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as reqerror:
        logger.error(f"Request Error: {reqerror.args[0]}")

    campaigns = {}
    if response.status_code == 200:
        campaigns = response.json()["campaigns"]

    # create pandas dataframe from dict
    campaign_df = pd.DataFrame()
    for thecampaign in campaigns:
        # store campaign general info
        camp_df = pd.DataFrame(
            data=[
                {
                    "campaign": thecampaign["name"],
                    "campaign_brevo_id": thecampaign["id"],
                    "sent_date": datetime.fromisoformat(thecampaign["sentDate"]),
                }
            ]
        )

        # aggregate statistics per campaign instead of per distribution list
        stats_list = thecampaign["statistics"]["campaignStats"]
        stat_df = pd.DataFrame()
        for stat in stats_list:
            # remove distribution list id
            stat.pop("listId", None)
            if stat_df.empty:
                stat_df = pd.DataFrame([stat])
            else:
                stat_df += pd.DataFrame([stat])

        if campaign_df.empty:
            campaign_df = pd.DataFrame(data=pd.concat([camp_df, stat_df], axis=1))
        else:
            campaign_df = pd.concat(
                [campaign_df, pd.DataFrame(data=pd.concat([camp_df, stat_df], axis=1))]
            )

    # write statistics to file
    campaign_df.to_csv(csv)


def main():
    parser = argparse.ArgumentParser(
        prog="newsletter.py",
        description="Aggregate newsletter statistics from brevo.com",
    )
    parser.add_argument("csv", type=pathlib.Path)
    parser.add_argument("--log", type=str, required=False, default="warning")
    args = parser.parse_args()

    # configure logging
    loglevel = args.log
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {loglevel}")
    logging.basicConfig(level=numeric_level)

    # check csv file path
    csv_path = args.csv
    if not csv_path.name.endswith(".csv"):
        logger.error("Provided file is not supported. Please provide .csv file.")
        logger.debug(f"Provided csv filepath was {csv_path}")
        return

    # get brevo API key
    try:
        BREVO_API_KEY = os.environ["BREVO_API_KEY"]
    except KeyError:
        logger.error("No brevo API Key found.")

    get_campaign_stats(apikey=BREVO_API_KEY, csv=csv_path)


if __name__ == "__main__":
    main()
