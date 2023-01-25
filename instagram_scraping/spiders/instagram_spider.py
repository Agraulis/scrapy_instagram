import scrapy
from scrapy.http import HtmlResponse
import re
from urllib.parse import urlencode
from copy import deepcopy
from items import InstagramScrapingItem

from login import USERNAME, PASSWORD, insta_users
"""
USERNAME, PASSWORD - str
insta_users - iterable(str)
"""


class InstagramSpider(scrapy.Spider):
    name = 'instagram_spider'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    insta_login_link = 'https://www.instagram.com/api/v1/web/accounts/login/ajax/'
    # user_for_scraping = insta_users[0]
    user_followers_and_following = {
        'user_info': {
            'user_name': None,
            'user_id': None,
        },
        'followers': [],
        'following': [],
    }

    def parse(self, response: HtmlResponse, **kwargs):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.insta_login_link,
            method='POST',
            callback=self.login,
            formdata={
                'enc_password': PASSWORD,
                'username': USERNAME,
                'queryParams': '{"__coig_restricted":"1"}',
                # 'queryParams': '',
                'optIntoOneTap': 'false',
                'trustedDeviceRecords': '{}',
            },
            headers={
                'X-CSRFToken': csrf,
            }
        )

    def login(self, response: HtmlResponse, **kwargs):
        j_data = response.json()
        if j_data.get('authenticated'):
            for user_for_scraping in insta_users:
                yield response.follow(
                    f'https://www.instagram.com/api/v1/users/web_profile_info/?username={user_for_scraping}',
                    callback=self.get_user_info,
                    cb_kwargs={'user_name': deepcopy(user_for_scraping)},
                )

    def get_user_info(self, response: HtmlResponse, **kwargs):
        j_data = response.json()
        user_id = j_data.get('data').get('user').get('id')
        user_full_name = j_data.get('data').get('user').get('full_name')
        self.user_followers_and_following['user_id'] = deepcopy(user_id)
        self.user_followers_and_following['user_name'] = deepcopy(user_full_name)
        yield response.follow(
            f'https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count=12&search_surface=follow_list_page',
            callback=self.followers_data_parse,
            cb_kwargs={
                'user_id': deepcopy(user_id),
                'user_name': deepcopy(kwargs.get('user_name')),
            },
        )
        yield response.follow(
            f'https://www.instagram.com/api/v1/friendships/{user_id}/following/?count=12',
            callback=self.following_data_parse,
            cb_kwargs={
                'user_id': deepcopy(user_id),
                'user_name': deepcopy(kwargs.get('user_name')),
            },
        )

    def followers_data_parse(self, response: HtmlResponse, **kwargs):
        j_data = response.json()
        next_max_id = j_data.get('next_max_id')
        user_id = kwargs.get("user_id")
        variables = {
            'count': 12,
            'max_id': deepcopy(next_max_id),
            'search_surface': 'follow_list_page',
        }
        url_posts = f'https://www.instagram.com/api/v1/friendships/{user_id}/followers/?{urlencode(variables)}'

        if j_data.get('big_list'):
            yield response.follow(
                url_posts,
                callback=self.followers_data_parse,
                cb_kwargs={
                    'variables': deepcopy(variables),
                    'user_id': deepcopy(user_id),
                    'user_name': deepcopy(kwargs.get('user_name')),
                }
            )
        yield InstagramScrapingItem(
            username=deepcopy(kwargs.get('user_name')),
            user_id=deepcopy(kwargs.get('user_id')),
            followers=deepcopy(j_data.get('users'))
        )

    def following_data_parse(self, response: HtmlResponse, **kwargs):
        j_data = response.json()
        next_max_id = deepcopy(j_data.get('next_max_id'))
        user_id = deepcopy(kwargs.get("user_id"))
        variables = {
            'count': 12,
            'max_id': deepcopy(next_max_id),
        }
        url_posts = f'https://www.instagram.com/api/v1/friendships/{user_id}/following/?{urlencode(variables)}'

        if j_data.get('big_list'):
            yield response.follow(
                url_posts,
                callback=self.following_data_parse,
                cb_kwargs={
                    'variables': deepcopy(variables),
                    'user_id': deepcopy(user_id),
                    'user_name': deepcopy(kwargs.get('user_name')),
                }
            )
        yield InstagramScrapingItem(
            username=deepcopy(kwargs.get('user_name')),
            user_id=deepcopy(kwargs.get('user_id')),
            following=deepcopy(j_data.get('users'))
        )

    def fetch_csrf_token(self, text):
        try:
            matched = re.search('\"csrf_token\\\\\":\\\\\"\\w+', text).group()
        except AttributeError:
            return None
        return matched.split('"')[-1]

    def fetch_next_max_id(self, text):
        try:
            matched = re.search('\"next_max_id\":\"\\d+_\\d+', text).group()
        except AttributeError:
            return None
        return matched.split('"')[-1]
