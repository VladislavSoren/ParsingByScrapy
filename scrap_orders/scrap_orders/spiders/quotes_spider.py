from collections import OrderedDict

import pandas as pd
import scrapy


class GoodUrlsSpider(scrapy.Spider):
    name = "quotes"
    target_categories_urls = OrderedDict()
    goods_category_urls = []
    max_page_num = 0
    current_page_index = 0
    category_path_gen = None
    START_URL = "https://order-nn.ru/kmo/catalog"
    BASE_URL = "https://order-nn.ru"

    def __init__(self, target_categories=None, SAVE_PATH=None, *args, **kwargs):
        super(GoodUrlsSpider, self).__init__(*args, **kwargs)
        self.target_categories = target_categories
        self.SAVE_PATH = SAVE_PATH

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

        # go to start page goods one of the category
        yield scrapy.Request(category_url_abs, callback=self.parse_goods_category_urls_list)

    # parsing urls goods with pagination
    def parse_goods_category_urls_list(self, response):
        # find max page number
        page_urls = response.xpath(
            "//div[@class='top-control']/div/ul[@class='ul-pagination']/li/a[@rel='canonical']/@href"
        ).getall()
        self.max_page_num = int(max(page_urls)[-1])

        # add good urls to shared storage
        self.goods_category_urls += response.xpath("//a[@itemprop='url']/@href").getall()

        # get next page because we have got info from first
        page_url_pagen_base = page_urls[0][:-1]  # '/kmo/catalog/5974/?PAGEN_1='
        self.current_page_index = 2
        next_page_url_rel = page_url_pagen_base + str(self.current_page_index)  # .../kmo/catalog/5974/?PAGEN_1=2
        next_page_url_abs = self.BASE_URL + next_page_url_rel

        # go to cycle parsing all urls of current category
        yield scrapy.Request(next_page_url_abs, callback=self.parse_goods_for_one)

    def parse_goods_for_one(self, response):
        # receiving goods links from current page
        self.goods_category_urls += response.xpath("//a[@itemprop='url']/@href").getall()

        # increment page number
        self.current_page_index += 1
        next_page_url_abs = response.url[:-1] + str(self.current_page_index)

        # if we parsed last category page -> go to the next category
        if self.current_page_index > self.max_page_num:
            try:
                category, url_path_rel = next(self.category_path_gen)
                category_url_abs = self.BASE_URL + url_path_rel
                yield scrapy.Request(category_url_abs, callback=self.parse_goods_category_urls_list)
            # condition of exit: category_path_gen is finished
            except StopIteration:
                data = pd.DataFrame({"goods_urls": self.goods_category_urls})
                data.to_csv(self.SAVE_PATH, index=False)
        # if not -> go to the next page
        else:
            try:
                yield scrapy.Request(
                    next_page_url_abs,
                    meta={
                        "dont_redirect": True,
                    },
                    callback=self.parse_goods_for_one,
                )
            except Exception as e:
                print(e)
