# from pathlib import Path

import scrapy

# from bs4 import BeautifulSoup


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    target_categories = {
        "Краски и материалы специального назначения",
        "Краски для наружных работ",
        "Лаки",
    }
    target_categories_urls = {}

    def start_requests(self):
        BASE_URL = [
            "https://order-nn.ru/kmo/catalog/",
        ]
        for url in BASE_URL:
            yield scrapy.Request(url=url, callback=self.parse)

    @staticmethod
    def normalise_str(value):
        value = value.strip().lower()
        return value

    def parse(self, response):
        for quote in response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]/div/div/a"):
            if not self.target_categories:
                break

            category_name = quote.css("a::text").get()  # quote.xpath('./text()').get()

            if category_name in self.target_categories:
                self.target_categories_urls[category_name] = quote.css("a::attr(href)").get()  # quote.attrib['href']
                self.target_categories.remove(category_name)

        yield self.target_categories


# /html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[2]
# /html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[2]


# sel = Selector(text='Лакокрасочные материалы')
# sel.css("div.col-md-11 col-sm-11 col-xs-11").get()

# response.css("div.col-md-11 col-sm-11 col-xs-11").get()

# response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]").extract()

# response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]/div[0]")


"""
col-md-4 col-sm-4 col-xs-4
response.xpath("//div[contains(@class,'col-md-4 col-sm-4 col-xs-4')]")

response.xpath("//div[contains(@class,'col-md-4 col-sm-4 col-xs-4')]")[0]
/html/body/div[6]/div[1]/div/div/div/div[1]/div[1]
/html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[1]

# next block
response.xpath("//div[contains(@class,'col-md-4 col-sm-4 col-xs-4')]")[1]
/html/body/div[6]/div[1]/div/div/div/div[1]/div[2]

response.xpath("//div[contains(@class,'col-md-4 col-sm-4 col-xs-4')]/div[1]")



1. Detect index of block
response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]/div/h2/a/text()") ->
all selects with big content blocks names (Лакокрасочные материалы: ..., Инструмент...)
2. Find index block with match
2. Build target block path by index
target_block_select = response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]")[0]
                    /html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[2]
                    /html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[2]/div[2]/div/a - target
3. Find inner block with goods
target_block_select.xpath("/div/a")

# proper path
/html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[2]/div[2]/div/a

/html/body/div[6]/div[1]/div/div/div/div[1]/div[1]
/html/body/div[6]/div[1]/div/div/div/div[1]/div[2]

/html/body/div[6]/div[1]/div/div/div/div[1]/div[1]/div[2]

>>> response.xpath("//div[contains(@class,'col-md-11 col-sm-11 col-xs-11')]/div[1]")


"""
