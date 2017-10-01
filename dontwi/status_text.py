# -*- coding: utf-8 -*-
"""Status text processor
"""
import re
from enum import Enum
from functools import reduce
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from unshortenit import unshorten

class TextType(Enum):
    WORDS = 0
    URL = 1
    HASHTAG = 2


class SplitedText(object):
    def __init__(self, text, text_type):
        self.text = text
        self.text_type = text_type


class StatusText(object):
    """description of class"""

    federation_hashtag = "don_tw"
    url_pattern = re.compile(r"(https?://[\w/:%#@\$&\?\(\)~\.=\+\-]+|#\S+)")

    def __init__(self, config):
        self.config = config

    @staticmethod
    def count_url_characters(url):
        unshorted_uri, status = unshorten(url)
        return sum([len(s) for s in urlparse(unshorted_uri)[0:2]]) + 3
        # +3 means length of "://"

    def slice_content_and_count_len(self, status_string):
        splited_text = self.url_pattern.split(status_string)
        for index in [0,-1]:
            if splited_text[index] == "":
                del splited_text[index]  
        marked_parts = [
            SplitedText(text=s, text_type=(lambda q:
                                           TextType.WORDS if not self.url_pattern.match(q)
                                           else TextType.URL if not q.startswith("#")
                                           else TextType.HASHTAG)(s))
            for s in splited_text]
        words = [s.text for s in marked_parts if s.text_type is TextType.WORDS]
        urls = [s.text for s in marked_parts if s.text_type is TextType.URL]
        hashtags = [
            s.text for s in marked_parts if s.text_type is TextType.HASHTAG]
        char_count = sum([len(p) for p in words])\
            + sum([len(p) for p in hashtags]) \
            + sum([self.count_url_characters(u) for u in urls])
        return marked_parts, char_count

    def replace_trigger_tag(self, status_string, hashtag):
        result = status_string.replace("#{0}".format(hashtag), "#{0}".format(self.federation_hashtag))
        return result

    @staticmethod
    def append_user_info(status_string, toot):
        modified_str = "{0}\n{1}".format(toot.get_user_account(), status_string)
        return modified_str

    @staticmethod
    def strip_html_tags(toot):
        soup = BeautifulSoup(toot.status["content"], "html.parser")
        for a_p in soup.find_all("p"):
            for a_br in a_p.find_all("br"):
                a_br.string = "\n"
            a_p.string = a_p.text + "\n"
        status_str = ("".join(soup.strings)).rstrip("\n")
        return status_str

    @staticmethod
    def trunc_redundant_line_break(status_string):
        result = re.sub(" *\n", "\n", status_string)
        return result

    @staticmethod
    def get_delimiter(str):
        if "\n" in str:
            return "\n"
        return " "

    def trim_text(self, status_str):
        limit_len = self.config.getint("message_length", 140)
        marked_parts, char_count = self.slice_content_and_count_len(status_str)
        remain = limit_len - char_count
        if remain < 0:
            marked_parts.reverse()
            for a_phrase in marked_parts:
                if a_phrase.text_type is TextType.WORDS:
                    len_phrase = len(a_phrase.text)
                    if len_phrase + remain < 1:
                        a_phrase.text = self.get_delimiter(a_phrase.text)
                        remain += len_phrase - 1
                    else:
                        a_phrase.text = a_phrase.text[0:len_phrase + remain]
                        if re.compile("\s$").search(a_phrase.text):
                            remain = 0
                            break
                        else:
                            delimiter = self.get_delimiter(a_phrase.text[len_phrase + remain - 1:-1])
                            if len_phrase + remain > 0:
                                a_phrase.text = a_phrase.text[:-1] + delimiter
                                remain = 0
                                break
                            else:
                                a_phrase.text[0] = delimiter
                                remain = -1
            marked_parts.reverse()
            if remain < 0:
                return None
        status_str = "".join([s.text for s in marked_parts])
        return status_str

    @staticmethod
    def remove_media_url(status_string, toot):
        return reduce(lambda str, media_dc:
            str.replace(media_dc["text_url"], ""), toot.get_medias(),
            status_string)

    def make_tweet_string_from_toot(self, toot, hashtag):
        if not "spoiler_text" in toot.status\
                or not toot.status["spoiler_text"]:
            result = self.strip_html_tags(toot)
        else:
            result = "{0} #{1}"\
                     .format(toot.status["spoiler_text"],
                             self.federation_hashtag)
        if not self.config.getboolean("attach_media_url", True):
            result = self.remove_media_url(result, toot)
        result = self.replace_trigger_tag(result, hashtag)
        result = self.trunc_redundant_line_break(result)
        result = self.append_user_info(result, toot)
        result = self.trim_text(result)

        return result
