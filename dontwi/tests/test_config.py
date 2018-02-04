#!  /usr/bin/python3
# -*- coding: utf-8 -*-
import codecs
import configparser
import os
import unittest

from ..config import Config


class TestConfig(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        remove_dummy_config_file()

    def test_load(self):
        f_name = make_dummy_config_file()
        config = Config()
        config.filename = f_name
        is_ng = config.load()
        self.assertFalse(is_ng)
        sections = config.items.sections()
        self.assertEqual(sections,
                         ["operation",
                          "endpoint your_mastodon",
                          "endpoint dontwi",
                          "result log",
                          "system log"])

    def test_save(self):
        conf = make_loaded_dummy_config()
        os.remove(conf.filename)
        conf.save()
        conf2 = Config()
        conf2.filename = conf.filename
        conf2.load()
        for a_section_str in conf.items.sections():
            for a_option_str in conf.items[a_section_str]:
                self.assertEqual(conf.items[a_section_str][a_option_str],
                                 conf2.items[a_section_str][a_option_str])

    def test_has_required_params(self):
        conf = Config()
        conf.load_config_file()
        is_ng = conf.has_required_options()
        self.assertTrue(is_ng)


def make_loaded_dummy_config(your_mastodon_fqdn=None, your_hashtag=None):
    f_name = make_dummy_config_file(your_mastodon_fqdn=your_mastodon_fqdn,
                                    your_hashtag=your_hashtag)
    conf = Config()
    conf.filename = f_name
    conf.load()
    return conf


def make_dummy_config_file(your_mastodon_fqdn=None, your_hashtag=None):
    config_str = '''
[operation]
inbound = your_mastodon
trigger = hashtag:your_hashtag
outbound = dontwi

[endpoint your_mastodon]
type = mastodon
api_base_url = https://your_mastodon.domain
client_name = dontwi
app_name = dontwi
since =

[endpoint dontwi]
type = twitter
app_key =
app_secret =
oauth_token =
oauth_token_secret =
message_length = 280

[result log]
db_file = ./_dontwi_log.db

[system log]
handler = StreamHandler
 '''
    if your_mastodon_fqdn is not None:
        config_str = config_str.replace(
            'your_mastodon.domain', your_mastodon_fqdn)
    if your_hashtag is not None:
        config_str.replace('your_hashtag', your_hashtag)
    cf_parser = configparser.ConfigParser()
    cf_parser.read_string(config_str)
    f_name = "_dontwi.ini"
    with codecs.open(f_name, "w", "utf-8") as cf_file:
        cf_parser.write(cf_file)
    return f_name


def remove_dummy_config_file():
    f_names = ['_dontwi.ini', '_dontwi_log.db']
    for f_name in f_names:
        if os.path.isfile(f_name):
            os.remove(f_name)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
