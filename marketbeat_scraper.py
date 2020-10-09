#!/usr/bin/python3


"""
-------------------------------------------------------------------------
                            BROKERAGE ACTIONS
-------------------------------------------------------------------------
This script gathers today's analyst actions (upgrades, downgrades, etc.)
of major brokerage houses for US companies (including OTC markets).

Source: www.marketbeat.com
-------------------------------------------------------------------------
"""


__author__  = 'Zsolt Forray'
__license__ = 'MIT'
__version__ = '0.0.1'
__date__    = '29/11/2019'
__status__  = 'Development'


import requests
from bs4 import BeautifulSoup as bs
import regex as re
from urllib.parse import urljoin


# 1. Earnings
# 2. upgrades and downgrades
# 3. recent news
# [11:41 AM]
# Need to know if we can scrub for this data easy(edited)
# [11:42 AM]
# and auto assign if it is bullish and bearish
# [11:48 AM]
# 4. dividend dates




class RSSNewsItem:
    def __init__(self, item):
        self.item = item

    @property
    def title(self):
        return self.item.title.get_text(strip=True)
    @property
    def link(self):
        return self.item.link
    @property
    def pubdate(self):
        return self.item.pubdate.get_text(strip=True)
    @property
    def description(self):
        return self.item.description.get_text(strip=True)

    @property
    def ticker(self):
        tickerPattern = re.compile(r"""
        \(NYSE:\s*([A-Z]+)\)  # OPEN PARENTH, FOLLOWED BY 'NYSE:' FOLLOWED BY OPTIONAL SPACING, FOLLOWED BY ONE OR MORE CAPITAL LETTERS, AND A CLOSING PARENTH
        """, flags=re.VERBOSE)
        tickerSearch = tickerPattern.search(self.title)
        if tickerSearch:
            return tickerSearch.group(1)
        else:
            return None




class NewsScraper:
    ## TODO: Enable sort by date and time.
    ## TODO: Get news for a particular ticker.
    ## TODO: Filter for most recent news

    def __init__(self):
        self.RSSUrl = "https://www.marketbeat.com/rss.ashx?type=headlines"
        #FIND SOURCES ELEMENT AND SET ALL SOURCES ATTRIBUTES

    def getRSSNewsFeed(self):
        """
        :return: a list of dictionaries containing the headlines  from the RSS News Feed
        """
        response = requests.get(self.RSSUrl)
        soup = bs(response.text)
        items = soup.select("item")
        headlines = []
        for thing in items:
            RSSItem = RSSNewsItem(thing)
            headlines.append(dict(
                Title=RSSItem.title,
                Description = RSSItem.description,
                PublicationDate = RSSItem.pubdate,
                Link = RSSItem.link
            ))
        return headlines



class RatingsScraper:
    ## TODO: Display to Discord filtered by High Impact
    ##TODO: Enable individual ticker upgrade queries
    ## TODO: Target Price 1.5x current price filter. Upgrade Alert
    ## TODO: Current Price x .7 >= target price # Downgrade Alert
    def __init__(self):
        self.url = "https://www.marketbeat.com/ratings/us/"

    def get_soup(self):
        """
        Request the MarketBeat Ratings Page.
        Create a BeautifulSoup Object from the Page's HTML.
        Store it in an attribute
        :return: None
        """
        # Get BeautifulSoup object
        CONNECT_TIMEOUT = 100
        READ_TIMEOUT = 100
        self.req = requests.get(url=self.url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        self.soup = bs(self.req.content, "lxml")

    def get_raw_table(self):
        """
        Use the soup object to find all "table" tags.
        Store the list of tags in an attribute.
        :return: None
        """
        # Get raw data table
        self.table_soup = self.soup.find_all("table")

    @staticmethod
    def get_table(table_soup):
        """
        Given the BeautifulSoup object of the table tags,
        go through the list of tables and return the first one.
        :param table_soup:
        :return: BeautifulSoup Object containing tags in the First Table
        """
        for table in table_soup:
            return table

    @staticmethod
    def actions():
        """

        :return: Tuple of possible actions from analysts
        """
        return ("Downgraded", "Upgraded", "Target Raised", "Target Lowered", \
                "Target Set", "Reiterated", "Initiated")

    @staticmethod
    def get_company(ticker, cols, index):
        """

        :param ticker: Ticker Symbol for a particular company.
        :param cols:
        :param index:
        :return:
        """
        if not RatingsScraper.check_empty_col(cols[index]):
            return cols[index].replace(ticker, "")

    @staticmethod
    def get_action(cols, index):
        if not RatingsScraper.check_empty_col(cols[index]):
            return cols[index].replace("by", "")

    @staticmethod
    def get_brokerage(cols, index):
        if not RatingsScraper.check_empty_col(cols[index]):
            return cols[index]

    @staticmethod
    def get_prices(cols, index):
        if not RatingsScraper.check_empty_col(cols[index]):
            price = cols[index].replace(" \u279D ", "/") # change (->)
            price = re.sub("^[$]\d+\/|^[$]\d+\.\d+\/", "", price)
            pattern = "\d+\.\d+|\d+"
            return float(re.findall(pattern, price)[0])

    @staticmethod
    def get_rating(cols, index):
        """
        Given a list of columns, return data from specific index.
        :param cols:
        :param index:
        :return:
        """
        if not RatingsScraper.check_empty_col(cols[index]):
            rating = cols[index].replace(" \u279D ", "/") # change (->)
            return re.sub("\w+\/|\w+\s\w+\/", "", rating)

    @staticmethod
    def check_empty_col(cell):
        if cell == "":
            return True

    def get_rows(self):
        """
        Go through the ratings table.
        Check for actions.
        Create attributes for the data from each company.
        Get the data
        :return:
        """
        table = RatingsScraper.get_table(self.table_soup)
        actions = RatingsScraper.actions()

        self.result_list = []
        for row in table.find_all("tr")[1:]: # header excluded
            if any(i in row.text for i in actions) \
               and "C$" not in row.text and "$" in row.text:
                self.ticker = row.find_all("div", class_="ticker-area")[0].text
                cols = [i.text for i in row]
                self.company = RatingsScraper.get_company(self.ticker, cols, 0)
                self.action = RatingsScraper.get_action(cols, 1)
                self.brokerage = RatingsScraper.get_brokerage(cols, 2)
                self.current_price = RatingsScraper.get_prices(cols, 3)
                self.target_price = RatingsScraper.get_prices(cols, 4)
                self.rating = RatingsScraper.get_rating(cols, 5)
                self.impact = RatingsScraper.get_rating(cols, 6)
                result_dict = self.collect_result()
                self.result_list.append(result_dict)

    def collect_result(self):
        return dict(ticker=self.ticker, company=self.company, action=self.action,\
                    brokerage=self.brokerage, current_price=self.current_price,\
                    target_price=self.target_price, rating=self.rating, impact=self.impact)

    def run_app(self):
        self.get_soup()
        self.get_raw_table()
        self.get_rows()
        return self.result_list

class EarningsScraper:
    ##TODO: Enable proximity to earnings date calulation.
    def __init__(self, tickr):
        self.genericURL = f"https://www.marketbeat.com/stocks/{tickr}"
        self.stockURL = requests.get(self.genericURL).url
        self.earningsURL = urljoin(self.stockURL, "earnings/")

    def getEarnings(self):
        resp = requests.get(self.earningsURL)
        soup = bs(resp.text)
        tables = soup.select("div.clearfix table")
        earningsTableRows = tables[1].select('tbody tr')
        results = []
        for row in earningsTableRows:
            cols = row.select("td")
            if len(cols) < 9: # Skip rows that do not contain any data
                continue
            earnings = Earnings(cols)
            results.append(dict(
                Date=earnings.date(),
                Quarter = earnings.quarter(),
                EstEPS = earnings.consensusEstimate(),
                RepEPS = earnings.reportedEPS(),
                EstRev = earnings.estRevenue(),
                ActRev = earnings.actRevenue()
            ))
        return results

class Earnings:
    def __init__(self, cols):
        self.cols = cols

    def date(self):
        return self.cols[0].get_text(strip=True)

    def quarter(self):
        return self.cols[1].get_text(strip=True)

    def consensusEstimate(self):
        return self.cols[2].get_text(strip=True)

    def reportedEPS(self):
        return self.cols[3].get_text(strip=True)

    def gaapEPS(self):
        return self.cols[4].get_text(strip=True)

    def estRevenue(self):
        return self.cols[5].get_text(strip=True)

    def actRevenue(self):
        return self.cols[6].get_text(strip=True)

    def details(self):
        return self.__dict__()

if __name__ == "__main__":
    mbs = RatingsScraper()
    mbs.run_app()
