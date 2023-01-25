# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class InstagramScrapingPipeline:
    def __init__(self):
        client = MongoClient('localhost:27017')
        self.mongo_db = client['instagram']

    def process_item(self, item, spider):
        collection = self.mongo_db[spider.name]

        username = item.get('username')
        user_id = item.get('user_id')
        followers = item.get('followers')
        following = item.get('following')

        updated_category = followers or following
        updated_category_name = 'followers' if followers else 'following'

        query = {'username': username, 'user_id': user_id}
        update = {'$push': {updated_category_name: updated_category}}

        try:
            collection.update_one(query, update, upsert=True)
        except Exception as e:
            print(e)
        return item
