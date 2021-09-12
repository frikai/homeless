import datetime
import time
from msedge.selenium_tools import EdgeOptions
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Edge
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.support.select import Select


class Ad:
    def __init__(self, id: int, posted: str, url: str):
        self.id: int = id
        self.posted: str = posted
        self.url: str = url
        self.time: datetime = datetime.datetime.now().replace(microsecond=0)

    def __str__(self):
        return 'New Ad: posted on %s, discovered on %s \n%s' % (self.posted, self.time, self.url)


def get_new(driver: WebDriver, seen: list, new: list):
    while True:
        try:
            idgen = (x.get_attribute("id") for x in driver.find_elements_by_xpath("//li[@class='search-result-entry "
                                                                                  "search-mate-entry']/a[1]"))
            dategen = (x.text for x in
                       driver.find_elements_by_xpath("//span[@class='create-date left-image-result']/strong"))
            urlgen = (x.get_attribute("href") for x in driver.find_elements_by_xpath("//li[@class='search-result-entry "
                                                                                     "search-mate-entry']/a[2]"))
            adgen = zip(idgen, dategen, urlgen)

            for ad in (Ad(*adtuple) for adtuple in adgen):
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
    select.select_by_visible_text("400")
    select = Select(driver.find_element_by_name("priceMax"))
    select.select_by_visible_text("1'000")
    select = Select(driver.find_element_by_id("selector-state"))
    select.select_by_visible_text(area)
    driver.find_element_by_id("selector-state").submit()


def main():
    seen: list = []
    new: list = []
    options = EdgeOptions()
    options.
    options.add_argument(r'--user-data-dir=C:\Users\julix\AppData\Local\Microsoft\Edge\User Data\\')
    driver = Edge(options)
    area_list = ["Zürich (Stadt)", "Zürich  (Oerlikon, Seebach, Affoltern)"]
    for area in area_list:
        search(driver, area)
        get_new(driver, seen, new)
    driver.close()


if __name__ == '__main__':
    main();

