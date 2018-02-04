#!  /usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
from sys import argv

from ..config import Config
from ..connector import MastodonConnector, TwitterConnector
from ..dontwi import Dontwi, get_secret_and_save
from .test_config import make_loaded_dummy_config, remove_dummy_config_file
from .test_result_log import make_dummy_conf_and_result_log


class TestDontwi(unittest.TestCase):

    def setUp(self):
        self.your_mastodon_fqdn = 'vocalodon.net'
        self.config, self.h_tag, self.tt_status, self.tw_status,\
            self.status_pr, self.result_log, self.status_str,\
            self.summary = make_dummy_conf_and_result_log(
                your_mastodon_fqdn=self.your_mastodon_fqdn)

    def tearDown(self):
        remove_dummy_config_file()

    def test_run(self):
        dontwi = Dontwi(self.config)
        is_ng = dontwi.run(is_dry_run=True)
        self.assertFalse(is_ng)

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
