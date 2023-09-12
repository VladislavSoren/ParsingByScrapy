"""
наименование
цена
описание
характеристики* в виде JSON.
"""
import logging
import sys
from collections import OrderedDict

import pandas as pd
import scrapy

# from ..items import GoodItem

# Параметры логирования
logging.basicConfig(
    filemode="w",
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d%H:%M:%S",
    level=logging.INFO,
)
parsing_logger = logging.getLogger(__name__)
logging.info("start")


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    target_categories = {
        "Краски и материалы специального назначения",
        "Краски для наружных работ",
        "Лаки",
    }
    target_categories_urls = OrderedDict()
    goods_category_urls = []
    max_page_num = 0
    current_page_index = 0
    category_path_gen = None
    START_URL = "https://order-nn.ru/kmo/catalog"
    BASE_URL = "https://order-nn.ru"

    def start_requests(self):
        yield scrapy.Request(url=self.START_URL, callback=self.pars_target_categories_urls)

    # receiving categories urls
    def pars_target_categories_urls(self, response):
        # form categories urls dict
        for quote in response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]/div/div/a"):
            if not self.target_categories:
                break

            category_name = quote.xpath("./text()").get()

            if category_name in self.target_categories:
                self.target_categories_urls[category_name] = quote.attrib["href"]
                self.target_categories.remove(category_name)

        # trigger scrab
        self.category_path_gen = iter(self.target_categories_urls.items())
        category, url_path_rel = next(self.category_path_gen)
        category_url_abs = self.BASE_URL + url_path_rel

        yield scrapy.Request(category_url_abs, callback=self.parse_goods_category_urls_list)

    # parsing urls goods with pagination
    def parse_goods_category_urls_list(self, response):
        # find max page number
        page_urls = response.xpath(
            "//div[@class='top-control']/div/ul[@class='ul-pagination']/li/a[@rel='canonical']/@href"
        ).getall()
        self.max_page_num = int(max(page_urls)[-1])

        self.goods_category_urls += response.xpath("//a[@itemprop='url']/@href").getall()

        page_url_pagen_base = page_urls[0][:-1]  # '/kmo/catalog/5974/?PAGEN_1='
        self.current_page_index = 2
        next_page_url_rel = page_url_pagen_base + str(self.current_page_index)  # .../kmo/catalog/5974/?PAGEN_1=2
        next_page_url_abs = self.BASE_URL + next_page_url_rel

        yield scrapy.Request(next_page_url_abs, callback=self.parse_goods_for_one)

    def parse_goods_for_one(self, response):
        # receiving goods links from current page
        self.goods_category_urls += response.xpath("//a[@itemprop='url']/@href").getall()

        # increment page number
        self.current_page_index += 1
        next_page_url_abs = response.url[:-1] + str(self.current_page_index)

        # condition of exit
        if self.current_page_index > self.max_page_num:
            try:
                category, url_path_rel = next(self.category_path_gen)
                category_url_abs = self.BASE_URL + url_path_rel
                yield scrapy.Request(category_url_abs, callback=self.parse_goods_category_urls_list)
            except StopIteration:
                data = pd.DataFrame({"goods_urls": self.goods_category_urls})
                path = "scrap_orders/spiders/goods_urls.csv"
                data.to_csv(path, index=False)

        else:
            try:  # why its doesnt work?! when page doesnt exist, no proc redirect?
                yield scrapy.Request(
                    next_page_url_abs,
                    meta={
                        "dont_redirect": True,
                    },
                    callback=self.parse_goods_for_one,
                )
            except Exception as e:
                print(e)


class GoodsSpider(scrapy.Spider):
    name = "goods"
    target_categories = {
        "Краски и материалы специального назначения",
        "Краски для наружных работ",
        "Лаки",
    }
    target_categories_urls = pd.read_csv("goods_urls.csv")
    BASE_URL = "https://order-nn.ru"
    SAVE_PATH = "goods.csv"
    good_index = 0
    START_URL = BASE_URL + target_categories_urls.values[good_index][0]  # https://order-nn.ru/kmo/catalog/5992/535730'

    def start_requests(self):
        # creating start table
        good_info = {}

        good_info["name"] = []
        good_info["price"] = []
        good_info["descr"] = []
        good_info["characteristics"] = []

        df_new = pd.DataFrame(good_info)
        df_new.to_csv(self.SAVE_PATH, index=False, header=True)

        yield scrapy.Request(url=self.START_URL, callback=self.pars_goods)

    # receiving categories urls
    def pars_goods(self, response):
        print("___Start pars_goods")

        # good_info = GoodItem()
        good_info = {}
        good_info["name"] = [response.xpath("//h1[@itemprop='name']/text()").get()]
        good_info["price"] = [response.xpath("//span[@class='element-current-price-number']/text()").get()]
        good_info["descr"] = [response.xpath("//div[@id='for_parse']/p/text()").get()]
        good_info["characteristics"] = ["empty"]

        # check item
        # yield good_info

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
