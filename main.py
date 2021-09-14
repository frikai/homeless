import datetime
import json
import os
import smtplib
import ssl
import time
from typing import List

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.support.select import Select

load_dotenv()


class Ad:
    def __init__(self, *args):
        self.time: datetime = datetime.datetime.now().replace(microsecond=0)

        if len(args) > 1:
            ad_id, posted, url, area = args
        else:
            dict_ad = args[0]
            ad_id = dict_ad["id"]
            posted = dict_ad["posted"]
            url = dict_ad["url"]
            area = dict_ad["area"]
            self.time = dict_ad["time"]

        self.id: int = ad_id
        self.posted: str = posted
        self.url: str = url
        self.area: str = area

    def __str__(self) -> str:
        return ('New room in %s, posted on %s, discovered on %s \n%s'
                % (self.area, self.posted, self.time, self.url)).replace("ü", "ue")

    def __eq__(self, other):
        if isinstance(other, Ad):
            return self.id == other.id
        return False

    def to_dict(self) -> dict:
        return {"id": self.id, "posted": self.posted, "url": self.url, "area": self.area, "time": str(self.time)}


class Sender:
    def __init__(self):
        self.port = 465
        self.from_address = os.getenv("sender_email")
        self.to_address = os.getenv("receiver_email")
        self.context = ssl.create_default_context()

    def send_update(self, ad_list: List[Ad]):
        l: int = len(ad_list)
        msg = f"Subject: Found {l} new {'ad' if l == 1 else 'ads'} wgzimmer.ch\n"
        for ad in ad_list:
            msg += str(ad) + "\n\n"

        with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=self.context) as server:
            server.login(self.from_address, os.getenv("password"))
            server.sendmail(self.from_address, self.to_address, msg)


def get_new(driver: WebDriver, seen: List[Ad], new: List[Ad], area: str):
    while True:
        try:
            idgen = (x.get_attribute("id") for x in driver.find_elements_by_xpath("//li[@class='search-result-entry "
                                                                                  "search-mate-entry']/a[1]"))
            dategen = (x.text for x in
                       driver.find_elements_by_xpath("//span[@class='create-date left-image-result']/strong"))
            urlgen = (x.get_attribute("href") for x in driver.find_elements_by_xpath("//li[@class='search-result-entry "
                                                                                     "search-mate-entry']/a[2]"))
            adgen = zip(idgen, dategen, urlgen)

            for ad in (Ad(*adtuple, area) for adtuple in adgen):
                if ad not in seen:
                    seen.append(ad)
                    new.append(ad)
            next_page(driver)
        except NoSuchElementException:
            break


def next_page(driver: WebDriver):
    next_button = driver.find_element_by_id("gtagSearchresultNextPage")
    next_button.click()


def search(driver: WebDriver, area: str):
    try:
        (driver.find_element_by_id("gtagSearchresultStartOverBottom")).click()
    except NoSuchElementException:
        driver.get("https://www.wgzimmer.ch/de/wgzimmer/search/mate.html?")
    select = Select(driver.find_element_by_name("priceMin"))
    select.select_by_visible_text(os.getenv("price_min"))
    select = Select(driver.find_element_by_name("priceMax"))
    select.select_by_visible_text(os.getenv("price_max"))
    select = Select(driver.find_element_by_id("selector-state"))
    select.select_by_visible_text(area)
    (driver.find_element_by_xpath("//div[@class='button-wrapper button-etapper']//input")).click()


def write_ad_list_to_json(new: List[Ad]):
    data = {"ads": [ad.to_dict() for ad in new]}
    with open('seen_ads.txt', 'w') as outfile:
        json.dump(data, outfile)


def load_json_to_ad_list() -> List[Ad]:
    try:
        print("loading json data of previous scans")
        with open('seen_ads.txt') as json_file:
            data: dict = json.load(json_file)
    except FileNotFoundError:
        print("Cannot find any previous records, looks like this is the first time you're running this.\n"
              "If that is not the case, the file I was storing seen ads in somehow got lost or moved :(\n"
              "Anyway, I'm making a new one ¯\\_(ツ)_/¯\n")
        print("creating \"seen_ads.txt\"")
        create_file()

        with open('seen_ads.txt') as json_file:
            data: dict = json.load(json_file)

    return [Ad(ad) for ad in data["ads"]]


def create_file():
    f = open("seen_ads.txt", "x")
    f.close()
    data = {"ads": []}
    with open('seen_ads.txt', 'w') as outfile:
        json.dump(data, outfile)


def main():
    seen: List[Ad] = load_json_to_ad_list()
    area_list = [os.getenv("area_1"), os.getenv("area_2")]
    sender = Sender()
    while True:
        print("starting a scan")
        driver = webdriver.Edge()
        new: List[Ad] = []
        for area in area_list:
            search(driver, area)
            get_new(driver, seen, new, area)
        if len(new) > 0:
            print(f"found {len(new)} new ads, sending via mail")
            sender.send_update(new)
            print("saving...")
            write_ad_list_to_json(seen)
        else:
            print("no new ads detected")
        print("done")
        print("-----------------------------------------------------------")
        driver.close()
        time.sleep(os.getenv("SEARCH_INTERVAL_SECONDS"))


if __name__ == '__main__':
    main()

# TODO: comments
# TODO: include template .env
# TODO: headless (switch to chrome driver?)
