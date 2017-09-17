# -*- coding: utf-8 -*-
"""Configuration manager
"""
import codecs
import configparser
import os
from functools import reduce
from operator import and_
from exception import DontwiConfigError, DontwiNotImplementedError


class Config(object):
    """
    This class has a configparser instance which has configuration options and related methods.
    Other classes get option values through this instance.
    """
    filename = "dontwi.ini"
    search_path = [".", "../etc"]
    required_params = {
        "endpoint mastodon": ["client_name", "api_base_url"],
        "endpoint twitter": ["app_key", "app_secret", "oauth_token",
                             "oauth_token_secret"],
        "operation": ["inbound", "outbound", "trigger"],
        "result log": ["db_file"],
        "system log": []
    }

    def __init__(self, items=None):
        self.items = items

    def search_config_file(self):
        if self.filename == "":
            return True
        else:
            if os.path.exists(self.filename):
                return False
            for a_pt in self.search_path:  # first match
                c_pt = os.path.join(a_pt, self.filename)
                if os.path.exists(c_pt):
                    self.filename = c_pt
                    return False
            return True

    def init_config(self):
        items = configparser.ConfigParser()
        rq_params = self.required_params
        for a_section in rq_params:
            items.add_section(a_section)
            for a_option in rq_params[a_section]:
                items[a_section][a_option] = ""
        self.items = items
        return False

    def load_config_file(self):
        self.items = configparser.ConfigParser()
        if self.search_config_file():
            return True
        [file_name] = self.items.read(self.filename, encoding="utf-8")
        if file_name != self.filename:
            return True
        return False

    def save(self):
        with codecs.open(self.filename, "w", "utf-8") as config_file:
            self.items.write(config_file)
        return False

    def has_required_sections(self):
        rq_sections = [a_section for a_section in self.required_params
                       if not a_section.startswith("endpoint ")]
        has_sections = reduce(and_, [a_section in self.items.sections()
                                     for a_section in rq_sections])
        return has_sections

    def has_required_endpoint_sections(self):
        rq_endpoint_sections = [
            "endpoint {0}".format(self.items["operation"][direction])
            for direction in ["inbound", "outbound"]]
        has_sections = reduce(and_, [a_section in self.items.sections()
                                     for a_section in rq_endpoint_sections])
        return has_sections

    def has_required_options(self):
        """Returns True if it contains all the options required in the configuration.
        """
        rq_params = self.get_requred_params()
        not_contained = [
            (section_str, option_str) for section_str in rq_params
            for option_str in rq_params[section_str]
            if not option_str in self.items[section_str]]
        return not not_contained

    def get_requred_params(self):
        """Returns required options of each sections
        """
        rq_params = {}
        for a_section in self.items.sections():
            if not a_section.startswith("endpoint "):
                key_of_sections = a_section
                if key_of_sections in self.required_params:
                    rq_params[a_section] = self.required_params[key_of_sections]
            else:
                if "type" in self.items[a_section]:
                    if self.items[a_section]["type"] in [
                            "twitter", "mastodon"]:
                        rq_params[a_section] = self.required_params[
                            "endpoint {0}".format(self.items[a_section]["type"])]
                    else:
                        raise DontwiNotImplementedError
                else:
                    rq_params[a_section] = ["type"]
        return rq_params

    def load(self):
        if self.load_config_file():
            raise DontwiConfigError
        if not self.has_required_sections():
            raise DontwiConfigError
        if not self.has_required_options():
            raise DontwiConfigError
        if not self.has_required_endpoint_sections():
            raise DontwiConfigError
        return False

    @property
    def inbound(self):
        return self.items[
            "endpoint {0}".format(
                self.items["operation"]["inbound"])]

    @property
    def outbound(self):
        return self.items[
            "endpoint {0}".format(
                self.items["operation"]["outbound"])]
