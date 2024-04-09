from dataclasses import asdict, dataclass, fields
from playwright.sync_api import sync_playwright, Playwright
from selectolax.parser import HTMLParser
from rich import print
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from timeit import default_timer as timer


@dataclass
class Listing:
    name: str
    beds: str
    date: str
    price: float


def run(playwright: Playwright):
    start = timer()
    try:
        # location = input("Enter location (e.g., california--United-States): ")
        # start_date = input("Enter start date (YYYY-MM-DD): ")
        # end_date = input("Enter end date (YYYY-MM-DD): ")

        location = "california--United-States"
        start_date = "2024-04-15"
        end_date = "2025-04-20"

        # Convert start and end dates to datetime objects
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        while start_date <= end_date:
            check_in = start_date.strftime("%Y-%m-%d")
            check_out = (start_date + timedelta(days=7)).strftime("%Y-%m-%d")

            start_url = (
                "https://www.airbnb.com/s/"
                + location
                + "/homes?checkin="
                + check_in
                + "&checkout="
                + check_out
            )
            chrome = playwright.chromium
            browser = chrome.launch(
                headless=False
            )  # launching headless so we can see the browser
            page = browser.new_page()  # page object to interact with
            page.goto(start_url)  # go to the page
            page.wait_for_timeout(1000)  # ensure the browser loads before terminating

            bnb_type_elements = page.locator(
                "div[data-testid='listing-card-title']"
            ).all()  # obtain all the bnb property type
            listing_elements = page.locator(
                "div[data-testid='listing-card-subtitle']"
            ).all()  # obtain all the data about the listings
            pricing_elements = page.locator(
                "span[class='_1y74zjx']"
            ).all()  # obtain all the data about the listing prices

            bnb_list = scraping_data(
                bnb_type_elements, listing_elements, pricing_elements, check_in
            )  # scrapes the data then return a list of bnb listings that can be work with

            print(panda_clean(bnb_list))
            # df = pd.read_csv('bnb_listings.csv')
            # Add a month to the date
            # Move to the next month, considering shifting to the next year
            start_date += relativedelta(months=1)
            if start_date.month == 1 and start_date.year != end_date.year:
                start_date = start_date.replace(
                    year=start_date.year + 1
                )  # Move to the next year  # Check if it's January
        end = timer()  # End the timer
        print(f"Runtime: {end - start} seconds")
    except Exception as e:
        print(f"An error occurred: {e}")


def panda_clean(data_array):
    df = pd.DataFrame(data_array)
    # format the date column as 'YYYY/MM/DD'
    # split name columns into type of bnb and location of bnb
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.strftime("%Y/%m/%d")
    df[["type", "location"]] = df["name"].str.split(" in ", expand=True)

    # drop the original 'name' column
    df.drop(columns=["name"], inplace=True)

    # reorder the columns and make it more visually clean
    df = df[["type", "location", "beds", "date", "price"]]
    df.columns = df.columns.str.capitalize()
    export_to_csv(df)
    export_to_json(df)
    return df


def scraping_data(bnb_type_elements, listing_elements, pricing_elements, check_in):
    Names = []
    Bedings = []
    Pricings = []
    Airbnbs = []

    for property_type in bnb_type_elements:
        Names.append(property_type.text_content().strip())

    for idx, (listing) in enumerate(listing_elements, start=1):
        listing_data = listing.text_content()

        if check_string(listing_data):
            Bedings.append(listing_data[:2])

    for price in pricing_elements:
        data = price.text_content().replace("\xa0", "").replace("$", "").strip()
        Pricings.append(data)

    for idx, (name, beding, price) in enumerate(zip(Names, Bedings, Pricings), start=0):
        new_listing = Listing(
            name=name,
            beds=beding,
            date=check_in,
            price=price,
        )
        Airbnbs.append(asdict(new_listing))

    return Airbnbs


def check_string(values):
    if values and values[0].isdigit():
        return True
    return False


def export_to_json(df):
    df.to_json("bnb_listings.json", orient="records", indent=4)


def export_to_csv(df):
    df.to_csv("bnb_listings.csv", index=False)


with sync_playwright() as playwright:
    run(playwright)
