#!  /usr/bin/python3
# -*- coding: utf-8 -*-
import re
import unittest
from json import dumps, loads
import string
import random

from ..connector import TootStatus
from ..status_text import StatusText
from ..exception import StatusTextError
from .test_config import make_loaded_dummy_config, remove_dummy_files


class TestStatusText(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        remove_dummy_files()

    def test_make_tweet_string(self):
        conf = make_loaded_dummy_config()
        status_text = StatusText(conf.outbound)
        for a_toot_dc in dummy_toot_dicts():
            status = TootStatus(a_toot_dc)
            status_str = status_text.make_tweet_string_from_toot(
                status, hashtag=a_toot_dc["hashtag"])
            self.assertFalse(status_str is None)
            ret = status_text.slice_content_and_count_len(status_str)
            self.assertTrue(
                ret[1] <= conf.items['endpoint dontwi'].getint('message_length'))
            hashtag_str = "#{0}".format(a_toot_dc["hashtag"])
            has_original_hashtag = re.search(
                "\S{0}".format(hashtag_str), status_str)
            self.assertFalse(has_original_hashtag, msg=status_str)
            has_federation_hashtag = re.search("\S{0}".format(
                status_text.federation_hashtag), status_str)
            self.assertTrue(has_federation_hashtag, msg=status_str)

    def test_remove_media_url(self):
        conf = make_loaded_dummy_config()
        status_text = StatusText(conf.outbound)
        for a_toot_dc in dummy_toot_with_media():
            status = TootStatus(a_toot_dc)
            text_url = status.get_medias()[0]["text_url"]
            conf.outbound["attach_media_url"] = "yes"
            status_str = status_text.make_tweet_string_from_toot(status,
                                                                 hashtag=a_toot_dc["tags"][0]["name"])
            self.assertGreater(status_str.count(text_url), 0)
            conf.outbound["attach_media_url"] = "no"
            status_str = status_text.make_tweet_string_from_toot(status,
                                                                 hashtag=a_toot_dc["tags"][0]["name"])
            self.assertEqual(status_str.count(text_url), 0)

    def test_spoiler_text(self):
        conf = make_loaded_dummy_config()
        status_text = StatusText(conf.outbound)
        toots_with_spoiler_text = [a_toot_dc for a_toot_dc in dummy_toot_dicts()
                                   if "spoiler_text" in a_toot_dc and a_toot_dc["spoiler_text"] != ""]
        for a_toot_dc in toots_with_spoiler_text:
            status = TootStatus(a_toot_dc)
            status_str = status_text.make_tweet_string_from_toot(
                status, hashtag=a_toot_dc["hashtag"])
            self.assertFalse(status_str is None)
            status_str2 = "@your_name@your_mastodon.domain\nyour spoiler text #don_tw"
            self.assertEqual(status_str, status_str2)

    def test_make_thread_tweets_from_toot(self):
        conf = make_loaded_dummy_config()
        limit_len=conf.items.getint('endpoint dontwi', 'message_length')
        conf.items.set('endpoint dontwi', 'post_mode', 'thread')
        status_text = StatusText(conf.outbound)
        for a_toot_dc in dummy_toot_dicts():
            status = TootStatus(a_toot_dc)
            hashtag_str = "#{0}".format(a_toot_dc["hashtag"])
            status_strs = status_text.make_tweet_string_from_toot(
                status, hashtag=a_toot_dc["hashtag"])
            self.assertFalse(status_strs is None)
            for status_str in status_strs:
                ret = status_text.slice_content_and_count_len(status_str)
                self.assertTrue(ret[1] <= limit_len)

    def test_make_thread_tweets_from_toot_by_long_words(self):
        word_len = 20
        conf = make_loaded_dummy_config()
        conf.items.set('endpoint dontwi', 'post_mode', 'thread')
        status_text = StatusText(conf.outbound)
        for a_toot_dc in dummy_toot_dicts2(word_len):
            account_match = re.match( r'http.*://(?P<instance>.*)/@(?P<name>.*)', a_toot_dc["account"]["url"])
            account_id = "@{0}@{1}".format(account_match.group('name'), account_match.group('instance'))
            #hashtag_str = "#{0}".format(a_toot_dc["hashtag"])
            hashtag_str =  "#{0}".format(StatusText.federation_hashtag)
            limit_len = len(account_id)+len(hashtag_str)+2+word_len
            conf.items['endpoint dontwi']["message_length"] = str(limit_len-1)    
            status = TootStatus(a_toot_dc)
            with self.assertRaises(StatusTextError):
                status_strs = status_text.make_tweet_string_from_toot(
                    status, hashtag=a_toot_dc["hashtag"])
                self.fail()
            conf.items['endpoint dontwi']["message_length"] = str(limit_len)
            status_strs = status_text.make_tweet_string_from_toot(
                    status, hashtag=a_toot_dc["hashtag"])
            self.assertFalse(status_strs is None)
            for status_str in status_strs:
                ret = status_text.slice_content_and_count_len(status_str)
                self.assertTrue(ret[1] <= limit_len)


def dummy_toot_dicts():
    dummy_toot_dicts = [{"hashtag": "your_hashtag", "account": {"url": "https://your_mastodon.domain/@your_name"},
                         "content": """<p>１２３４５６７８９０１２３４５６７８９０１２３４５６７８９０１２３４５６７８９０１２３４５６７８９０
            あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやぃゆぇよらりるれろわぃぅぇを
            １２３４５６７８９０１２３４５６７８９０１２３４５６７８９０１２３４５６７８９０１２３４５６７８９０
            https://aaa.bbb.com/ddd/eee/fff?ggg=hhh#iii=jjj 間隔 https://kkk.lll.mmm/nnn/ooo/ppp?qqq=rrr#sss=ttt
            <a>#<span>your_hashtag</span></a></p>"""},
                        {"hashtag": "your_hashtag", "account": {"url": "https://your_mastodon.domain/@your_name"},
                         "content": """<p>content text</p><p><a href="https://your_mastodon.domain/tags/%E3%81%A9%E3%82%93%E3%81%A4%E3%81%84" class="mention hashtag" rel="tag">#<span>your_hashtag</span></a></p>"""},
                        {"hashtag": "your_hashtag", "account": {"url": "https://your_mastodon.domain/@your_name"},
                         "spoiler_text": "your spoiler text",
                         "content": """<p>content text</p><p><a href="https://your_mastodon.domain/tags/%E3%81%A9%E3%82%93%E3%81%A4%E3%81%84" class="mention hashtag" rel="tag">#<span>your_hashtag</span></a></p>"""}]
    return dummy_toot_dicts


def dummy_toot_dicts2(test_len=15):
    hiragana_list = [chr(i) for i in range(12353, 12436)]
    zenkaku_digit_list = [chr(i) for i in range(65296, 65296+10)]

    content = "".join([string.ascii_letters[index]  for index in range(test_len)])
    content += "".join([hiragana_list[index] for index in range(test_len // 2)])
    content += " "
    content += "".join([zenkaku_digit_list[index % 10] for index in range(test_len // 2)])
    content += "".join([hiragana_list[index] for index in range(test_len // 2)])
    content += "\n"
    content += "".join([string.ascii_letters[index]  for index in range(test_len)])
    content += "".join([hiragana_list[index] for index in range(test_len // 2)])

    dummy_toot_dicts2 = [{"hashtag": "your_hashtag", "account": {"url": "https://your_mastodon.domain/@your_name"},
                         "content": "<p>{0}</p>".format(content)}]
    return dummy_toot_dicts2



def dummy_toot_with_media(your_mastodon_fqdn=''):
    dummy_toot_dicts = \
        [{
            "tags": [{
                "name": "your_hashtag"
            }],
            "account": {
                "url": "https://your_mastodon.domain/@your_name"
            },
            "media_attachments": [{
                "id": "176430",
                "remote_url": "",
                "type": "image",
                        "url": "https://your_mastodon.domain/system/media_attachments/files/000/176/430/original/0a1fe0114e651c11.png?1503076930",
                        "preview_url": "https://your_mastodon.domain/system/media_attachments/files/000/176/430/small/0a1fe0114e651c11.png?1503076930",
                        "text_url": "https://your_mastodon.domain/media/3PC20UvN6R82SG9J14A",
                        "meta": {
                            "original": {
                                "width": 1280,
                                "height": 960,
                                "size": "1280x960",
                                "aspect": 1.3333333333333333
                            },
                            "small": {
                                "width": 400,
                                "height": 300,
                                "size": "400x300",
                                "aspect": 1.3333333333333333
                            }
                        }
            }],
            "content": """<p>your_image<br /><a href=\"https://your_mastodon.domain/tags/your_hashtag" class=\"mention hashtag\" rel=\"tag\">#<span>your_hashtag</span></a><br /> <a href=\"https://your_mastodon.domain/media/3PC20UvN6R82SG9J14A\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"ellipsis\">your_mastodon.domain/media/3PC20UvN6R</span><span class=\"invisible\">82SG9J14A</span></a></p>"""
        },
            {
                "tags": [{
                    "name": "your_hashtag"
                }],
                "account": {
                    "url": "https://your_mastodon.domain/@your_name"
                },
                "media_attachments": [{
                    "id": "204575",
                    "remote_url": "",
                    "type": "video",
                    "url": "https://your_mastodon.domain/system/media_attachments/files/000/204/575/original/9cb9fe0e801db9a5.mp4?1504280244",
                    "preview_url": "https://your_mastodon.domain/system/media_attachments/files/000/204/575/small/9cb9fe0e801db9a5.png?1504280244",
                    "text_url": "https://your_mastodon.domain/media/3HpO5larDL_A-UyS1-Y",
                    "meta": {
                            "original": {
                                "width": 1980,
                                "height": 1080,
                                "size": "1980x1080",
                                "aspect": 1.8333333333333333
                            },
                        "small": {
                                "width": 400,
                                "height": 218,
                                "size": "400x218",
                                "aspect": 1.834862385321101
                                }
                    }
                }],
                "mentions": [],
                "content": "<p>your_video<br /><a href=\"https://your_mastodon.domain/tags/%E3%83%89%E3%83%AA%E3%83%AB%E3%83%89%E3%83%AA%E3%83%AB%E3%83%89%E3%83%AA%E3%83%AB\" class=\"mention hashtag\" rel=\"tag\">#<span>ドリルドリルドリル</span></a> <a href=\"https://your_mastodon.domain/media/3HpO5larDL_A-UyS1-Y\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"ellipsis\">your_mastodon.domain/media/3HpO5larDL</span><span class=\"invisible\">_A-UyS1-Y</span></a></p>"
        }]
    if your_mastodon_fqdn:
        dummy_toot_str = dumps(dummy_toot_dicts)
        dummy_toot_dicts = dummy_toot_dicts = loads(
            dummy_toot_str.replace('your_mastodon.domain', your_mastodon_fqdn))
    return dummy_toot_dicts
