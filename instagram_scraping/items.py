# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstagramScrapingItem(scrapy.Item):
    username = scrapy.Field()
    user_id = scrapy.Field()
    followers = scrapy.Field()
    following = scrapy.Field()
    _id = scrapy.Field()
