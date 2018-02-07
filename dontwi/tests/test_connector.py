#!  /usr/bin/python3
# -*- coding: utf-8 -*-
import json
import os
import unittest
from configparser import ConfigParser
from io import BytesIO

from magic import Magic

#from PIL import Image
from ..config import Config
from ..connector import MastodonConnector, TootStatus, TwitterConnector
from ..status_text import StatusText
from .test_config import remove_dummy_files
from .test_result_log import make_dummy_conf_and_result_log
from .test_status_text import dummy_toot_with_media

CONFIG_FOR_TESTS = ConfigParser()
CONFIG_FOR_TESTS_FILENAME = 'test.ini'
YOUR_MASTODON_FQDN = ''
if os.path.exists(CONFIG_FOR_TESTS_FILENAME):
    CONFIG_FOR_TESTS.read(CONFIG_FOR_TESTS_FILENAME, encoding='utf-8')
    if 'test' in CONFIG_FOR_TESTS:
        YOUR_MASTODON_FQDN = CONFIG_FOR_TESTS['test'].get(
            'your_mastodon_fqdn', YOUR_MASTODON_FQDN)


class TestConnector(unittest.TestCase):

    def setUp(self):
        self.config, self.h_tag, self.tt_status, self.tw_status,\
            self.status_pr, self.result_log, self.status_str,\
            self.summary = make_dummy_conf_and_result_log(YOUR_MASTODON_FQDN)

    def tearDown(self):
        remove_dummy_files()

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_register_to_mastodon(self):
        m_cn = MastodonConnector(self.config.items['endpoint your_mastodon'])
        self.assertFalse(m_cn.register_to_mastodon())

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_mastodon_connector(self):
        m_cn = MastodonConnector(self.config.items['endpoint your_mastodon'])
        self.assertIsInstance(m_cn, MastodonConnector)
        self.assertFalse(m_cn.connect())
        cl_sc_str = m_cn.config.get('client_secret')
        self.assertIsInstance(cl_sc_str, str)

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_get_statuses_by_ftag(self):
        status_text = StatusText(self.config.outbound)
        mastodon_cn = MastodonConnector(
            self.config.items['endpoint your_mastodon'])
        hashtag = CONFIG_FOR_TESTS['test_get_statuses_by_ftag']['hashtag']
        mastodon_cn.connect()
        test_id_status_st = json.loads(
            CONFIG_FOR_TESTS['test_get_statuses_by_ftag']['test_id_status_st'])
        for a_id in test_id_status_st:
            statuses_by_id = mastodon_cn.get_statuses_by_hashtag(
                hashtag, "id:{0}".format(int(a_id) - 1))
            status_by_id = next(statuses_by_id)
            status_st_by_id = status_text.make_tweet_string_from_toot(
                status_by_id, hashtag=hashtag) if status_by_id is not None else None
            statuses_by_ts = mastodon_cn.get_statuses_by_hashtag(
                hashtag, test_id_status_st[a_id][0])
            status_by_ts = next(statuses_by_ts)
            status_st_by_ts = status_text.make_tweet_string_from_toot(
                status_by_ts, hashtag=hashtag) if status_by_ts is not None else None
            self.assertEqual(test_id_status_st[a_id][1],
                             status_st_by_id,
                             status_st_by_ts)

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_get_statuses_by_hashtag(self):
        status_text = StatusText(self.config.outbound)
        mastodon_cn = MastodonConnector(
            self.config.items["endpoint your_mastodon"])
        hashtag = CONFIG_FOR_TESTS['test_get_statuses_by_hashtag']['hashtag']
        mastodon_cn.connect()
        test_id_status_st = json.loads(
            CONFIG_FOR_TESTS['test_get_statuses_by_hashtag']['test_id_status_st'])
        for a_id in test_id_status_st:
            statuses_by_id = mastodon_cn.get_statuses_by_hashtag(
                hashtag, "id:{0}".format(int(a_id) - 1))
            status_by_id = next(statuses_by_id)
            status_st_by_id = status_text.make_tweet_string_from_toot(
                status_by_id, hashtag=hashtag) if status_by_id is not None else None
            statuses_by_ts = mastodon_cn.get_statuses_by_hashtag(
                hashtag, test_id_status_st[a_id][0])
            status_by_ts = next(statuses_by_ts)
            status_st_by_ts = status_text.make_tweet_string_from_toot(
                status_by_ts, hashtag=hashtag) if status_by_ts is not None else None
            self.assertEqual(test_id_status_st[a_id][1],
                             status_st_by_id,
                             status_st_by_ts)

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_line_break(self):
        status_msg_proc = StatusText(self.config.outbound)
        mastodon_cn = MastodonConnector(
            self.config.items["endpoint your_mastodon"])
        hashtag = CONFIG_FOR_TESTS['test_line_break']['hashtag']
        mastodon_cn.connect()
        test_id_status_st = json.loads(
            CONFIG_FOR_TESTS['test_line_break']['test_id_status_st'])
        for a_id in test_id_status_st:
            since_id = "id:{0}".format(int(a_id) - 1)
            max_id = "id:{0}".format(int(a_id) + 1)
            statuses_by_id = mastodon_cn.get_statuses_by_hashtag(
                hashtag=hashtag, since=since_id, until=max_id)
            status_st_by_id = status_msg_proc.make_tweet_string_from_toot(
                next(statuses_by_id), hashtag=hashtag)
            self.assertEqual(test_id_status_st[a_id], status_st_by_id)

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    @unittest.skipUnless(
        'test_filter_mention' in CONFIG_FOR_TESTS, 'The value required by this method is not defined')
    def test_filter_mention(self):
        status_msg_proc = StatusText(self.config.outbound)
        mastodon_cn = MastodonConnector(
            self.config.items['endpoint your_mastodon'])
        hashtag = CONFIG_FOR_TESTS['test_filter_mention']['hashtag']
        mastodon_cn.connect()
        statuses_gn = mastodon_cn.get_statuses_by_hashtag(
            hashtag=hashtag, since="", until="")
        mention_status_id = CONFIG_FOR_TESTS['test_filter_mention']['mention_status_id']
        statuses = [a_status for a_status in statuses_gn]
        status_ids = [a_status.get_status_id() for a_status in statuses]
        self.assertNotEqual(int(status_ids[0]), mention_status_id)
        self.assertFalse(mention_status_id in status_ids)

    def test_twitter_connector(self):
        t_cn = TwitterConnector(self.config.items["endpoint dontwi"])
        self.assertIsInstance(t_cn, TwitterConnector)
        self.assertFalse(t_cn.connect())

    def test_mastodon_status_get_medias(self):
        toots = [TootStatus(a_dc)
                 for a_dc in dummy_toot_with_media()]
        for a_toot in toots:
            for a_media_dc in a_toot.get_medias():
                self.assertIn("text_url", a_media_dc)

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_get_media_ios(self):
        toots = [
            TootStatus(a_dc) for a_dc in dummy_toot_with_media(YOUR_MASTODON_FQDN)]
        mastodon_connector = MastodonConnector(
            self.config.items["endpoint your_mastodon"])
        magic = Magic(mime=True)
        for a_toot in toots:
            media_ios = mastodon_connector.get_media_ios(a_toot.get_medias())
            for a_io in media_ios:
                self.assertIsInstance(a_io, mastodon_connector.MediaIo)
                self.assertIsInstance(a_io.io, BytesIO)
                data = a_io.io.read(261)
                mime = magic.from_buffer(data)
                mime_prefix = mime.split("/")[0]
                self.assertIsNotNone(mime_prefix, a_io.type)
