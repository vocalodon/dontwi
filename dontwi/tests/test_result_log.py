#!  /usr/bin/python3
# -*- coding: utf-8 -*-
import json
import os.path
import unittest
from datetime import datetime

from dateutil.parser import parse as timestamp_parse
from tinydb import database

from ..connector import TootStatus, TweetStatus
from ..result_log import ResultLog
from ..status_text import StatusText
from .test_config import make_loaded_dummy_config, remove_dummy_files


class TestStatusLog(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        remove_dummy_files()

    def test_make_result_summary(self):
        config, h_tag, tt_status, tw_status,\
            status_msg_proc, result_log, status_str,\
            summary = make_dummy_conf_and_result_log()
        self.assertEqual(summary["inbound_status_id"],
                         tt_status.get_status_id())
        self.assertEqual(summary["outbound_status_id"],
                         tw_status.get_status_id())
        now_t_stamp = datetime.now().timestamp()
        processed_t_stamp = timestamp_parse(
            summary["processed_at"]).timestamp()
        self.assertAlmostEqual(now_t_stamp, processed_t_stamp, delta=1)

    def test_get_summaries_by_result(self):
        config, hashtag, tt_status, tw_status,\
            status_pr, result_log, status_str,\
            summary = make_dummy_conf_and_result_log()
        remove_file(config.items["result log"]["db_file"])
        dummy_id_to_result = {
            "10": "Test",
            "21": "Waiting",
            "32": "Failed",
            "43": "Succeed"}
        summaries = []
        for a_id in dummy_id_to_result:
            tt_status.status["id"] = a_id
            tw_str = status_pr.make_tweet_string_from_toot(
                tt_status, hashtag=hashtag)
            summary = make_result_summary(result_log=result_log, result=dummy_id_to_result[a_id],
                                          inbound_status=tt_status, outbound_status=tw_status,
                                          hashtag=hashtag, status_string=tw_str)
            summaries += [summary]
        result_log.save_result_summaries(summaries)
        for a_id in dummy_id_to_result:
            summaries2 = result_log.get_result_summaries_by_results(
                [dummy_id_to_result[a_id]])
            self.assertEqual(len(summaries2), 1)
            self.assertEqual(summaries2[0]["inbound_status_id"], a_id)

    def test_get_process_summary(self):
        config, h_tag, tt_status, tw_status,\
            status_pr, result_log, status_str,\
            summary = make_dummy_conf_and_result_log()
        remove_file(config.items["result log"]["db_file"])
        result_log.save_result_summaries(result_summaries=[summary])
        summaries = result_log.get_result_summaries_by_status(status=tt_status)
        self.assertEqual(tt_status.get_status_id(),
                         summaries[0]["inbound_status_id"])

    def test_has_result_of_message(self):
        config, hashtag, tt_status, tw_status,\
            status_pr, result_log, status_str,\
            summary = make_dummy_conf_and_result_log()
        has_result = result_log.has_result_of_status(
            status=tt_status, results=["Succeed", "Start"])
        self.assertTrue(has_result)

    def test_status(self):
        h_tag, tt_status, tw_status = get_dummy_materials()
        self.assertEqual(tt_status.status, tt_status._status)
        self.assertEqual(tw_status.status, tw_status._status)
        status_dict = tt_status.status
        status_dict["id"] = str(int(status_dict["id"]) + 1)
        tt_status.status = status_dict
        self.assertEqual(tt_status.get_status_id(), status_dict["id"])

    def test_dump_log(self):
        config, h_tag, tt_status, tw_status,\
            status_pr, result_log, status_str,\
            summary = make_dummy_conf_and_result_log()
        dump_str = result_log.dump_log()
        self.assertEqual(type(dump_str[0]), database.Element)
        self.assertIsInstance(json.dumps(dump_str), str)

    def test_remove_waiting(self):
        config, hashtag, tt_status, tw_status,\
            status_pr, result_log, status_str,\
            summary = make_dummy_conf_and_result_log()
        tt_status.status["id"] = 12
        tw_str = status_pr.make_tweet_string_from_toot(
            tt_status, hashtag=hashtag)
        summary = make_result_summary(result_log=result_log, result="Waiting",
                                      inbound_status=tt_status, outbound_status=tw_status,
                                      hashtag=hashtag, status_string=tw_str)
        result_log.save_result_summaries([summary])
        waiting_summaries = \
            result_log.get_result_summaries_by_results(["Waiting"])
        self.assertEqual(waiting_summaries[0]["result"], summary["result"])
        eids = [a_summary.eid for a_summary in waiting_summaries]
        result_log.remove_summaries_by_eids(eids)
        waiting_summaries2 = result_log.\
            get_result_summaries_by_results(["Waiting"])
        self.assertFalse(waiting_summaries2)

    def test_has_result_of_status(self):
        pass


def make_result_summary(result_log, inbound_status,
                        outbound_status, status_string, hashtag,
                        result):
    summary = result_log.make_result_and_others_summary(
        status_string=status_string, hashtag=hashtag, result=result)
    summary.update(result_log.make_status_summary("inbound",
                                                  status=inbound_status))
    summary.update(result_log.make_status_summary("outbound",
                                                  status=outbound_status))
    return summary


def get_dummy_materials():
    h_tag = "your_hashtag"
    tt_status = dummy_toot()
    tw_status = dummy_tweet()
    return h_tag, tt_status, tw_status


def make_dummy_conf_and_result_log(your_mastodon_fqdn=None):
    config = make_loaded_dummy_config(your_mastodon_fqdn)
    hashtag, tt_status, tw_status = get_dummy_materials()
    status_pr = StatusText(config.outbound)
    status_str = status_pr.make_tweet_string_from_toot(
        toot=tt_status, hashtag=hashtag)
    result_log = ResultLog(config.items)
    summary = result_log.make_result_and_others_summary(
        status_string=status_str, hashtag=hashtag, result="Succeed")
    summary.update(result_log.make_status_summary("inbound",
                                                  status=tt_status))
    summary.update(result_log.make_status_summary("outbound",
                                                  status=tw_status))
    remove_file(config.items["result log"]["db_file"])
    result_log.save_result_summaries(result_summaries=[summary])
    return config, hashtag, tt_status, tw_status,\
        status_pr, result_log, status_str,\
        summary


def remove_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def dummy_toot():
    return TootStatus(json.loads(r'''
{
    "id": "1345211",
    "created_at": "2017-07-06T18:37:16.703Z",
    "in_reply_to_id": null,
    "in_reply_to_account_id": null,
    "sensitive": false,
    "spoiler_text": "",
    "visibility": "public",
    "language": "ja",
    "application": null,
    "account": {
        "id": 292,
        "username": "your_name",
        "acct": "your_name",
        "display_name": "your_name",
        "locked": false,
        "created_at": "2017-04-17T09:02:09.993Z",
        "followers_count": 140,
        "following_count": 118,
        "statuses_count": 1893,
        "note": "<p></p>",
        "url": "https://your_mastodon.domain/@your_name",
        "avatar": "",
        "avatar_static": "",
        "header": "https://your_mastodon.domain/headers/original/missing.png",
        "header_static": "https://your_mastodon.domain/headers/original/missing.png"
    },
    "media_attachments": [],
    "mentions": [],
    "tags": [
        {
            "name": "your_hashtag",
            "url": "https://your_mastodon.domain/tags/your_hashtag"
        }
    ],
    "uri": "tag:your_mastodon.domain,2017-07-06:objectId=1345211:objectType=Status",
    "content": "<p><a href=\"https://your_mastodon.domain/tags/your_hashtag\" class=\"mention hashtag\" rel=\"tag\">#<span>your_hashtag</span></a><br />test toot</p>",
    "url": "https://your_mastodon.domain/@your_name/1345211",
    "reblogs_count": 0,
    "favourites_count": 0,
    "reblog": null
}
        '''))


def dummy_tweet():
    return TweetStatus(json.loads(r'''
{
    "created_at": "Thu Jul 06 18:54:11 +0000 2017",
    "id": 883036371132178432,
    "id_str": "883036371132178432",
    "text": "#your_hashtag\ntest toot",
    "truncated": false,
    "entities": {
        "hashtags": [
            {
                "text": "your_hashtag",
                "indices": [
                    0,
                    9
                ]
            }
        ],
        "symbols": [],
        "user_mentions": [],
        "urls": []
    },
    "source": "<a href=\"https://your_mastodon.domain/about\" rel=\"nofollow\">Dontwi</a>",
    "in_reply_to_status_id": null,
    "in_reply_to_status_id_str": null,
    "in_reply_to_user_id": null,
    "in_reply_to_user_id_str": null,
    "in_reply_to_screen_name": null,
    "user": {
        "id": 1,
        "id_str": "1",
        "name": "your_name",
        "screen_name": "your_name",
        "location": "",
        "description": "",
        "url": null,
        "entities": {
        },
        "protected": false,
        "followers_count": 437,
        "friends_count": 1215,
        "listed_count": 16,
        "created_at": "Tue Jan 04 14:19:14 +0000 2011",
        "favourites_count": 1887,
        "utc_offset": 32400,
        "time_zone": "Tokyo",
        "geo_enabled": false,
        "verified": false,
        "statuses_count": 8130,
        "lang": "ja",
        "contributors_enabled": false,
        "is_translator": false,
        "is_translation_enabled": false,
        "profile_background_color": "C0DEED",
        "profile_background_image_url": "http://abs.twimg.com/images/themes/theme1/bg.png",
        "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme1/bg.png",
        "profile_background_tile": false,
        "profile_image_url": "http://pbs.twimg.com/profile_images/3715255775/df0cac53fdd8ad62bc4cc967e3aee7b3_normal.png",
        "profile_image_url_https": "https://pbs.twimg.com/profile_images/3715255775/df0cac53fdd8ad62bc4cc967e3aee7b3_normal.png",
        "profile_link_color": "1DA1F2",
        "profile_sidebar_border_color": "C0DEED",
        "profile_sidebar_fill_color": "DDEEF6",
        "profile_text_color": "333333",
        "profile_use_background_image": true,
        "has_extended_profile": false,
        "default_profile": true,
        "default_profile_image": false,
        "following": false,
        "follow_request_sent": false,
        "notifications": false,
        "translator_type": "none"
    },
    "geo": null,
    "coordinates": null,
    "place": null,
    "contributors": null,
    "is_quote_status": false,
    "retweet_count": 0,
    "favorite_count": 0,
    "favorited": false,
    "retweeted": false,
    "lang": "ja"
}
        '''))
