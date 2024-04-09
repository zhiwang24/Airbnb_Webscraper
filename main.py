import httpx
from selectolax.parser import HTMLParser
import time
from urllib.parse import urljoin
from dataclasses import asdict, dataclass, fields
import json
import csv
import pandas as pd

@dataclass
class Item:
    name: str
    item_number: str
    price: str
    rating: float


def get_html(url, **kwargs):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    if kwargs.get("page"):
        resp = httpx.get(
            url + str(kwargs.get("page")), headers=headers, follow_redirects=True
        )
    else:
        resp = httpx.get(url, headers=headers, follow_redirects=True)

    try:
        resp.raise_for_status()
    except:
        return False

    html = HTMLParser(resp.text)
    return html


def extract_text(html, sel):
    try:
        text = html.css_first(sel).text()
        return text
    except AttributeError as err:
        return None


def parse_page(html):
    products = html.css("li.VcGDfKKy_dvNbxUqm29K")
    for product in products:
        yield urljoin("https://www.rei.com/", product.css_first("a").attributes["href"])


def parse_item_page(html):
    new_item = Item(
        name=extract_text(html, "h1#product-page-title"),
        item_number=extract_text(html, "span#product-item-number"),
        price=extract_text(html, "span#buy-box-product-price"),
        rating=extract_text(html, "span.cdr-rating__number_15-0-0"),
    )
    return asdict(new_item)


def export_to_json(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    print("Saved to JSON") 

def export_to_csv(products):
    field_names = [field.name for field in fields(Item)]
    with open("products.csv", "w") as f:
        writer = csv.DictWriter(f, field_names)
        writer.writeheader()
        writer.writerows(products)
    print("Saved to CSV")    

def append_to_csv(product):
    field_names = [field.name for field in fields(Item)]
    with open("appendcsv.csv", "a") as f:
        writer = csv.DictWriter(f, field_names)
        writer.writerows(product)
    print("Appended CSV")

def clean(values):
    chars_to_remove = ["$", "Item #"]
    for char in chars_to_remove:
        if char in values:
            values = values.replace(char, "")
    return values.strip() #remove white space


def main():
    products = []
    baseurl = "https://www.rei.com/c/camping-and-hiking/f/scd-deals?page="
    for x in range(1, 2):
        html = get_html(baseurl, page=x)
        if html == False:
            break
        print("Printing page: " + str(x))
        product_url = parse_page(html)
        print (product_url)
        for url in product_url:
            html = get_html(url)
            products.append(parse_item_page(html))
            time.sleep(0)

        export_to_json(products)
        export_to_csv(products)

        productcsv = pd.read_csv('products.csv')
        print(productcsv.head(5))


if __name__ == "__main__":
    main()
