import requests
import datetime
import os
import logging

import pandas as pd

TICKETMASTER_API_KEY = os.environ.get("TICKETMASTER_API_KEY")
if not TICKETMASTER_API_KEY:
    raise ValueError("Please set the TICKETMASTER_API_KEY environment variable.")


class TicketmasterAPI:
    """
    A class to interact with the Ticketmaster API.
    """

    BASE_API_URL = "https://app.ticketmaster.com/discovery/v2"

    def __init__(self, api_key: str):
        """
        Initializes the TicketmasterAPI with the provided API key.

        :param api_key: Your Ticketmaster API key.
        """

        self.api_key = api_key

    def _paginated_event_getter(self, items_per_page: int = 100, params: dict = None):
        """
        Generator function to fetch paginated events from the Ticketmaster API.

        :param items_per_page: The amount of items per page.
        :param params: Additional parameters for the API request.
        :return: A list of events.
        """

        page_number = 1

        if params is None:
            # Use default params
            events_until = datetime.date.today() + datetime.timedelta(weeks=4)
            params = {
                "countryCode": "NL",
                "endDateTime": events_until.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        params["apikey"] = self.api_key
        params["size"] = items_per_page

        while True:
            params["page"] = page_number
            response = requests.get(f"{self.BASE_API_URL}/events", params=params)
            response.raise_for_status()

            data = response.json()
            events = data.get("_embedded", {}).get("events", [])

            if not events:
                logging.info(f"No more events found on page {page_number}.")
                break

            yield data
            logging.info(f"Fetched {len(events)} events from page {page_number}.")

            page_number += 1

    def fetch_events(self, items_per_page: int = 100, params: dict = None):
        """
        Fetches events from the Ticketmaster API.

        :param items_per_page: The amount of items per page.
        :param params: Additional parameters for the API request.
        :return: A list of events.
        """

        all_events = []
        for data in self._paginated_event_getter(items_per_page, params):
            all_events.extend(data.get("_embedded", {}).get("events", []))

        return all_events

    def parse_events(self, events: list):
        """
        Parses the events and returns a list of dictionaries with relevant information.

        :param events: A list of events.
        :return: A list of dictionaries with relevant event information.
        """

        parsed_events = []
        for event in events:
            venue = event.get("_embedded", {}).get("venues", [{}])[0]
            promotor = event.get("promoter", {})
            dates = event.get("dates", {})

            parsed_event = {
                "id": event.get("id"),
                "name": event.get("name"),
                "url": event.get("url"),
                "date": dates.get("start", {}).get("localDate"),
                "time": dates.get("start", {}).get("localTime"),
                "timezone": event.get("dates", {}).get("timeZone"),
                "datetime": dates.get("start", {}).get("dateTime"),
                "venue": venue.get("name"),
                "city": venue.get("city", {}).get("name"),
                "country": venue.get("country", {}).get("name"),
                "postal_code": venue.get("postalCode"),
                "latitude": venue.get("location", {}).get("latitude"),
                "longitude": venue.get("location", {}).get("longitude"),
                "address": venue.get("address", {}).get("line1"),
                "promotor_id": promotor.get("name"),
            }
            parsed_events.append(parsed_event)

        return parsed_events


def extract_data():

    ticketmaster_api = TicketmasterAPI(TICKETMASTER_API_KEY)
    logging.info("Fetching events from Ticketmaster API...")
    events = ticketmaster_api.fetch_events()

    logging.info("Parsing events...")
    parsed_events = ticketmaster_api.parse_events(events)

    logging.info("Writing events to local CSV file...")
    datetime_now = datetime.datetime.now()
    file_name = f"{datetime_now.strftime('%Y%m%d%HH')}_events.csv"

    df_stg = pd.DataFrame(parsed_events)
    df_stg.to_csv(file_name, index=False)

    logging.info("Done!")


if __name__ == "__main__":
    extract_data()
