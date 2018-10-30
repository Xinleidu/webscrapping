#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


import datetime

from bs4 import BeautifulSoup
import pandas as pd
import splinter

CHROME_DRIVER = {
    'name': 'chrome',
    'path': 'chromedriver',
    'headless': True
}


class MarsDataFetcher(object):

    def __init__(self, conf):
        self._driver = splinter.Browser(conf['name'],
                                    executable_path=conf['path'],
                                    headless=conf['headless'])
        self._source_processors = [
            (MarsDataFetcher.fetch_news,
                'https://mars.nasa.gov/news/',
                ('news_title', 'news_p')),
            (MarsDataFetcher.fetch_featured_image,
                'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars',
                ('featured_image_url',)),
            (MarsDataFetcher.fetch_weather,
                'https://twitter.com/marswxreport?lang=en',
                ('mars_weather',)),
            (MarsDataFetcher.fetch_facts,
                'http://space-facts.com/mars/',
                ('facts',)),
            (MarsDataFetcher.fetch_hemispheres,
                'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars',
                ('hemisphere_image_urls',)),
        ]

    def __del__(self):
        self._driver.quit()

    def run(self):
        result = {}
        msg = 'success'
        for proc, source_url, fields in self._source_processors:
            try:
                print('Processing %s' % source_url)
                self._driver.visit(source_url)
                result.update({fields[i]: r for i, r in enumerate(proc(self._driver))})
            except Exception as e:
                result, msg = None, 'Error occurs in processing %s: %s' % (source_url, str(e))
                break
        if result is not None:
            result['create_time'] = datetime.datetime.now()
        return result, msg

    @staticmethod
    def fetch_news(driver):
        # Wait for presentation of list items
        driver.is_element_present_by_css('ul.item_list li.slide', wait_time=5.0)
        # select the latest news
        news = BeautifulSoup(driver.html, 'html.parser').select_one('ul.item_list li.slide')
        news_title = news.find('div', class_='content_title').get_text()
        news_p = news.find('div', class_='article_teaser_body').get_text()
        return news_title, news_p

    @staticmethod
    def fetch_featured_image(driver):
        full_image = driver.find_by_id('full_image')
        full_image.click()
        # Wait for presentation of 'more info' button
        driver.is_element_present_by_text('more info', wait_time=5.0)
        driver.find_link_by_partial_text('more info').click()
        image = BeautifulSoup(driver.html, 'html.parser').select_one('figure.lede a img')
        featured_image_url = 'https://www.jpl.nasa.gov%s' % image.get('src')
        return featured_image_url,

    @staticmethod
    def fetch_weather(driver):
        tweet = BeautifulSoup(driver.html, 'html.parser').find('div',
                attrs={'class': 'tweet', 'data-name': 'Mars Weather'}
            )
        mars_weather = tweet.find('p', 'tweet-text').get_text()
        return mars_weather,

    @staticmethod
    def fetch_facts(driver):
        df = pd.read_html(driver.html)[0]
        df.columns = ['description', 'value']
        df.set_index('description', inplace=True)
        return df.to_html(classes='table table-striped'),

    @staticmethod
    def fetch_hemispheres(driver):
        hemisphere_image_urls = []
        num_items = int(len(BeautifulSoup(driver.html, 'html.parser').find_all(class_='item')))
        for i in range(num_items):
            driver.find_by_css('a.product-item h3')[i].click()
            soup = BeautifulSoup(driver.html, 'html.parser')
            title = soup.find('h2', class_='title').get_text()
            img_url = soup.find('a', text='Sample').get('href')
            hemisphere_image_urls.append({'title': title, 'img_url': img_url})
            driver.back()
        return hemisphere_image_urls,


def scrape():
    """ scrape all data related to 'mission to mars'
    Args
        driver: web browser
    """
    fetcher = MarsDataFetcher(CHROME_DRIVER)
    result, msg = fetcher.run()
    return result, msg


if __name__ == '__main__':
    import pymongo
    mongo_client = pymongo.MongoClient('mongodb://localhost:27017/mission_to_mars')
    mission_to_mars = mongo_client.db.mission_to_mars
    result, msg = scrape()
    if result is not None:
        mission_to_mars.insert(result)
    print(msg)
    print(result)