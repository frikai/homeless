import datetime
import os
import smtplib
import ssl
from typing import List

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.support.select import Select

load_dotenv()


class Ad:
    def __init__(self, id: int, posted: str, url: str, area: str):
        self.id: int = id
        self.posted: str = posted
        self.url: str = url
        self.time: datetime = datetime.datetime.now().replace(microsecond=0)
        self.area: str = area

    def __str__(self) -> str:
        return 'New ad: posted on %s, discovered on %s \n%s' % (self.posted, self.time, self.url)


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


def main():
    seen: List[Ad] = []
    new: List[Ad] = []
    driver = webdriver.Edge()
    area_list = [os.getenv("area_1"), os.getenv("area_2")]
    sender = Sender()
    for area in area_list:
        search(driver, area)
        get_new(driver, seen, new, area)
    sender.send_update(new)
    driver.close()


if __name__ == '__main__':
    main()
