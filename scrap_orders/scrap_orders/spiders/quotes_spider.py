# from ..items import GoodItem
from collections import OrderedDict

import pandas as pd
import scrapy


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

    @staticmethod
    def first_element_iter_obj(s):
        return next(iter(s))

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
        # start_url = self.first_element_iter_obj(self.target_categories_urls)
        self.category_path_gen = iter(self.target_categories_urls.items())
        category, url_path_rel = next(self.category_path_gen)
        category_url_abs = self.BASE_URL + url_path_rel

        yield scrapy.Request(category_url_abs, callback=self.parse_goods_category_urls_list)

    # parsing urls goods with pagination
    def parse_goods_category_urls_list(self, response):
        # usefull work (scrab index page)

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
                path = "goods_urls.csv"
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


"""
next_page_url_rel = response.xpath(
    "//div[@class='top-control']/div/ul[@class='ul-pagination']/li/a[@rel='canonical']/@href")[-1].get()
next_page_url_abs = self.BASE_URL + next_page_url_rel

response.xpath("//div[@class='top-control']/div/ul[@class='ul-pagination']/li/a[@rel='canonical']/@href")[-1].get()

response.xpath("//ul[@class='ul-pagination']/li/a[@rel='canonical']/@href")[-1].get()

//ul[@class='ul-pagination']

response.xpath("//a[@itemprop='url']")

//a[@itemprop="url"] -> contains all goods urls from page

//div[@class="horizontal-product-item"] > to all good block

/html/body/div[6]/div/div/div[2]/div[2]/div/div[4]/div[1]/div[2]/div[3]/div[2]/a

наименование
цена
описание
характеристики* в виде JSON.

/html/body/div[6]/div/div/div[2]/div[2]/div/div[4]/div[1]
/html/body/div[6]/div/div/div[2]/div[2]/div/div[6]/div/div/div[3]
"""
