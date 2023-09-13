import time

from log_config import parsing_logger
from scrapy.crawler import CrawlerRunner
from spiders.goods_spider import GoodsSpider
from spiders.quotes_spider import GoodUrlsSpider
from twisted.internet import defer, reactor

runner = CrawlerRunner()


@defer.inlineCallbacks
def crawl():
    # prepare spider for goods url
    target_categories = {
        "Краски и материалы специального назначения",
        "Краски для наружных работ",
        "Лаки",
    }
    SAVE_PATH_URLS = "parsed_info/goods_urls.csv"

    time_start = time.time()
    parsing_logger.info("Start GoodUrlsSpider")
    yield runner.crawl(GoodUrlsSpider, target_categories=target_categories, SAVE_PATH=SAVE_PATH_URLS)
    parsing_logger.info(f"Finish GoodUrlsSpider, time: {time.time() - time_start}")

    # .....

    SAVE_PATH_INFO = "parsed_info/goods.csv"

    time_start = time.time()
    yield runner.crawl(GoodsSpider, SOURCE_PATH=SAVE_PATH_URLS, SAVE_PATH=SAVE_PATH_INFO)
    parsing_logger.info(f"Finish GoodsSpider, time: {time.time() - time_start}")

    reactor.stop()


crawl()
reactor.run()
