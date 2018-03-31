# -*- coding: utf-8 -*-
"""Status text processor
"""
import re
import regex
from enum import Enum
from functools import reduce

from bs4 import BeautifulSoup

from .exception import StatusTextError


class TextType(Enum):
    WORDS = 0
    URL = 1
    HASHTAG = 2


class SplitedText(object):
    def __init__(self, text, text_type):
        self.text = text
        self.text_type = text_type


class StatusText(object):
    """Status text processor"""

    federation_hashtag = "don_tw"
    url_pattern = re.compile(r"(https?://[\w/:%#@\$&\?\(\)~\.=\+\-]+|#\S+)")
    latin_pattern = regex.compile(r"([\p{N}\p{Latin}\p{P}]{1,140}|.|\s)")

    def __init__(self, config):
        self.config = config

    @staticmethod
    def codepoint_weight(codepoint):
        return 1 if ord(codepoint) < 0x1100 else 2  # quick hack
        # U+1100-11FF is Hangul Jamo
                                                          # block

    def weighted_length(self, text):
        weighted_length = sum([self.codepoint_weight(codepoint)
                               for codepoint in text])
        return weighted_length

    @staticmethod
    def count_url_characters(url):
        return 23
        #unshorted_uri, status = unshorten(url)
        # return sum([len(s) for s in urlparse(unshorted_uri)[0:2]]) + 3
        # +3 means length of "://"

    def length_of_part(self, part):
        if part.text_type is TextType.URL:
            return self.count_url_characters(part.text)
        if part.text_type is TextType.HASHTAG:
            return self.weighted_length(part.text)
        if part.text_type is TextType.WORDS:
            return self.weighted_length(part.text)
        raise StatusTextError

    def slice_content_and_count_len(self, status_string):
        splited_text = self.url_pattern.split(status_string)
        for index in [0, -1]:
            if splited_text[index] == "":
                del splited_text[index]
        marked_parts = []
        for text in splited_text:
            if text.startswith("#"):
                text_type = TextType.HASHTAG
            elif self.url_pattern.match(text):
                text_type = TextType.URL
            else:
                words = self.latin_pattern.findall(text)
                marked_parts.extend( [SplitedText(text=w, text_type=TextType.WORDS) for w in words])
                continue
            marked_parts.append( SplitedText(text=text, text_type=text_type))
        words = [s.text for s in marked_parts if s.text_type is TextType.WORDS]
        urls = [s.text for s in marked_parts if s.text_type is TextType.URL]
        hashtags = [
            s.text for s in marked_parts if s.text_type is TextType.HASHTAG]
        char_count = sum([self.length_of_part(p) for p in marked_parts])
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
    def get_delimiter(text):
        match = re.search(r'[\s]', text)
        if match:
            return match.group()
        return " "

    def trim_text(self, status_str):
        limit_len = self.config.getint("message_length", 280)
        marked_parts, char_count = self.slice_content_and_count_len(status_str)
        remain_capacity = limit_len - char_count
        if remain_capacity < 0:
            marked_parts.reverse()
            for a_phrase in marked_parts:
                if a_phrase.text_type is TextType.WORDS:
                    assert a_phrase.text
                    len_phrase = self.weighted_length(a_phrase.text)
                    if len_phrase + remain_capacity < 1:
                        a_phrase.text = self.get_delimiter(a_phrase.text)
                        remain_capacity += len_phrase - 1
                    else:
                        to_be_left = ''
                        index = None
                        for index, codepoint in enumerate(a_phrase.text):
                            weight = self.codepoint_weight(codepoint)
                            if len_phrase + remain_capacity - weight - 1 < 0:
                                index -= 1
                                break
                            to_be_left += codepoint
                            remain_capacity -= weight
                        delimiter = self.get_delimiter(a_phrase.text[index:])
                        a_phrase.text = to_be_left + delimiter
                        remain_capacity = 0
            marked_parts.reverse()
            if remain_capacity < 0:
                return None
        status_str = "".join([s.text for s in marked_parts])
        return status_str

    def concat_text_of_parts(self, parts):
        text = ''
        for a_part in parts:
            text += a_part.text
        return text

    def slice_text(self, header, marked_parts):
        """ Split the text of status every 280 characters """
        limit_len = self.config.getint("message_length", 280)
        length = 0
        text = ''
        header_tail = SplitedText('#{0}\n'.format(self.federation_hashtag), TextType.HASHTAG)
        header_all = header + [header_tail]
        header_len = sum(self.length_of_part(a_part) for a_part in header_all)
        #marked_parts = header + marked_parts
        for (index_of_part, part) in enumerate(marked_parts):
            part_len = self.length_of_part(part)
            if length + part_len + header_len <= limit_len:
                if part.text == "#"+self.federation_hashtag:
                    header_tail = SplitedText('\n', TextType.WORDS)
                    header_all = header + [header_tail]
                    header_len = sum(self.length_of_part(a_part) for a_part in header_all)
                text += part.text
                length += part_len
            else:
                return [self.concat_text_of_parts(header_all) + text] + self.slice_text(header, marked_parts[index_of_part:])
        if text:
            return [self.concat_text_of_parts(header_all) + text]
        else:
            return []

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

    def make_thread_tweets_from_toot(self, toot, hashtag):
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
        header = [SplitedText("{0} ".format(toot.get_user_account()),
                                TextType.WORDS)]
        marked_parts, char_count = self.slice_content_and_count_len(result)
        #tweet_strings = self.split_text(result)
        tweet_strings = self.slice_text(header, marked_parts)
        return tweet_strings