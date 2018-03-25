#!  /usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
from sys import argv
from twython import TwythonRateLimitError

from ..__main__ import get_secret_and_save
from ..config import Config
from ..connector import MastodonConnector, TwitterConnector, IConnector
from ..dontwi import Dontwi
from .test_config import make_loaded_dummy_config, remove_dummy_files
from .test_result_log import make_dummy_conf_and_result_log
from .test_connector import CONFIG_FOR_TESTS, CONFIG_FOR_TESTS_FILENAME, YOUR_MASTODON_FQDN


class TestDontwi(unittest.TestCase):

    def setUp(self):
        self.your_mastodon_fqdn = YOUR_MASTODON_FQDN
        self.config, self.h_tag, self.tt_status, self.tw_status,\
            self.status_pr, self.result_log, self.status_str,\
            self.summary = make_dummy_conf_and_result_log(
                your_mastodon_fqdn=self.your_mastodon_fqdn)

    def tearDown(self):
        remove_dummy_files()

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_run(self):
        dontwi = Dontwi(self.config)
        is_ng = dontwi.run(is_dry_run=True)
        self.assertFalse(is_ng)

    def test_process_one_waiting_status(self):
        dontwi = Dontwi(self.config)

        class DummyConnector():
            def connect(self, do_login=False):
                pass
            def update_status(self, status_string, media_ids):
                raise TwythonRateLimitError(msg="dummy", error_code=88)
            def upload_medias(self, media_ios):
                pass
            def get_media_ios(self, media_dicts):
                pass
        out_cn = DummyConnector()
        result_summaries = self.result_log.get_result_summaries_by_results(["Succeed"])
        target = result_summaries[0]
        dontwi.process_one_waiting_status(result_log=self.result_log, 
                                          result_summary=target, media_ios=None, 
                                          out_cn=out_cn,is_dry_run=False)
        result_strs = [result["result"] for result in result_summaries]
        self.assertNotEquals(result_strs, "Failed")

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_run_test_db(self):
        result_strs = ["Succeed", "Waiting", "Test"]
        summaries_dc = {a_result: self.result_log.get_result_summaries_by_results([a_result])
                        for a_result in result_strs}
        self.config.items["operation"]["trigger"] = "hashtag:" + \
            summaries_dc["Succeed"][0]["hashtag"]
        dontwi = Dontwi(self.config)
        is_ng = dontwi.run(is_dry_run=True)
        self.assertFalse(is_ng)
        summaries_dc2 = {a_result: self.result_log.get_result_summaries_by_results([a_result])
                         for a_result in result_strs}
        self.assertEqual(
            len(summaries_dc2["Test"]) - len(summaries_dc["Test"]), 1)
        self.assertGreater(len(summaries_dc2["Waiting"]),
                           len(summaries_dc["Waiting"]))
        self.assertEqual(len(summaries_dc2["Succeed"]),
                         len(summaries_dc["Succeed"]))

    @unittest.skipUnless(YOUR_MASTODON_FQDN,
                         'YOUR_MASTODON_FQDN isn\'t defined')
    def test_get_secret(self):
        is_ng = get_secret_and_save(self.config)
        self.assertFalse(is_ng)
        should_have_secrets = Config()
        should_have_secrets.filename = self.config.filename
        should_have_secrets.load()
        self.assertIsInstance(
            self.config.items["endpoint your_mastodon"]["client_secret"], str)
        self.assertEqual(self.config.items["endpoint your_mastodon"]["client_secret"],
                         should_have_secrets.items["endpoint your_mastodon"]["client_secret"])

    def test_get_connectors(self):
        self.config.load()
        dontwi = Dontwi(self.config)
        in_cn = dontwi.get_connector("inbound")
        out_cn = dontwi.get_connector("outbound")
        if self.config.items["endpoint " + self.config.items["operation"]
                             ["inbound"]]["type"] == "mastodon":
            self.assertIsInstance(in_cn, MastodonConnector)
        else:
            self.assertIsInstance(in_cn, TwitterConnector)
        if self.config.items["endpoint " + self.config.items["operation"]
                             ["outbound"]]["type"] == "mastodon":
            self.assertIsInstance(out_cn, MastodonConnector)
        else:
            self.assertIsInstance(out_cn, TwitterConnector)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
