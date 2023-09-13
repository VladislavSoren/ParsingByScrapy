import sys

import pandas as pd
import scrapy


class GoodsSpider(scrapy.Spider):
    name = "goods"
    target_categories_urls = None
    BASE_URL = "https://order-nn.ru"
    good_index = 0

    def __init__(self, SOURCE_PATH=None, SAVE_PATH=None, *args, **kwargs):
        super(GoodsSpider, self).__init__(*args, **kwargs)
        self.SOURCE_PATH = SOURCE_PATH
        self.SAVE_PATH = SAVE_PATH

    def start_requests(self):
        # create start table
        self.target_categories_urls = pd.read_csv(self.SOURCE_PATH)

        good_info = {}

        good_info["name"] = []
        good_info["price"] = []
        good_info["descr"] = []
        good_info["characteristics"] = []

        df_new = pd.DataFrame(good_info)
        df_new.to_csv(self.SAVE_PATH, index=False, header=True)

        # prepare START_URL and run pars_goods
        START_URL = self.BASE_URL + self.target_categories_urls.values[self.good_index][0]
        yield scrapy.Request(url=START_URL, callback=self.pars_goods)

    # receiving categories urls
    def pars_goods(self, response):
        print("___Start pars_goods")

        # good_info = GoodItem()
        good_info = {}
        good_info["name"] = [response.xpath("//h1[@itemprop='name']/text()").get()]
        good_info["price"] = [response.xpath("//span[@class='element-current-price-number']/text()").get()]
        good_info["descr"] = [response.xpath("//div[@id='for_parse']/p/text()").get()]
        good_info["characteristics"] = ["empty"]

        # save info
        df_new = pd.DataFrame(good_info)
        df_new.to_csv(self.SAVE_PATH, mode="a", index=False, header=False)

        # increment good_index
        self.good_index += 1
        print(self.good_index)

        # if we fall out our frame -> stop program
        try:
            next_url = self.BASE_URL + self.target_categories_urls.values[self.good_index][0]
        except IndexError:
            sys.exit()

        # to the next good
        yield scrapy.Request(url=next_url, callback=self.pars_goods)
