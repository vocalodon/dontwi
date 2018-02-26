#!  /usr/bin/python3
# -*- coding: utf-8 -*-
""" Entry point and main process control
"""
import json
import os
import re
from logging import StreamHandler, getLogger

from twython import TwythonError

from .config import Config
from .connector import MastodonConnector, TwitterConnector
from .exception import DontwiConfigError, DontwiNotImplementedError
from .result_log import ResultLog
from .status_text import StatusText
from .version import __version__


class Dontwi(object):

    def __init__(self, config):
        self.config = config
        self.setup_logger()

    def get_trigger(self):
        triger_str = self.config.items["operation"]["trigger"]
        parse_triger_word = re.match(
            "(?P<type>hashtag|keyword|user):(?P<word>.*)", triger_str)
        type_str = parse_triger_word.group("type")
        if type_str == "hashtag":
            word_str = parse_triger_word.group("word")
        elif type_str == "keyword" or type_str == "user":
            raise DontwiNotImplementedError
        else:
            word_str = triger_str
        return word_str

    def setup_logger(self):

        self.logger = getLogger(__name__)
        system_log_cf = self.config.items["system log"]
        if "log_level" in system_log_cf:
            self.logger.setLevel(system_log_cf["log_level"])
        if not "handler" in system_log_cf\
                or system_log_cf["handler"] in ["StreamHandler", ""]:
            self.logger.addHandler(StreamHandler(os.sys.stdout))
        elif system_log_cf["handler"] == "JournalHandler":
            from systemd import journal
            self.logger.addHandler(journal.JournaldLogHandler())
        else:
            raise DontwiNotImplementedError
        return False

    @staticmethod
    def summaries_to_be_listed(
            result_log, status_pr, statuses, trigger_str):
        summaries = []
        for a_status in statuses:
            # results's 2nd.  condition which match to "Start" is for
            # fail-safe.
            if not result_log.has_result_of_status(
                    status=a_status, results=["Succeed", "Start", "Failed", "Test"]):
                st_str = status_pr.make_tweet_string_from_toot(
                    a_status, hashtag=trigger_str)
                rs_str = "Waiting"
                rs_sm = result_log.make_result_and_others_summary(
                    status_string=st_str, hashtag=trigger_str, result=rs_str)
                in_sm = result_log.make_status_summary("inbound", a_status)
                rs_sm.update(in_sm)
                summaries.append(rs_sm)
        return summaries

    def fill_in_waiting_list(
            self, result_log, status_pr, statuses, triger_str):
        summaries = self.summaries_to_be_listed(
            result_log, status_pr, statuses, triger_str)
        eids = result_log.save_result_summaries(result_summaries=summaries)
        if eids is None:
            self.logger.debug("Failed to update log database.")
        return eids

    def process_one_waiting_status(self, result_log, result_summary, media_ios, out_cn,
                                   is_dry_run):
        result_summary["result"] = "Start"
        result_summary.update(result_log.get_processed_at_dict())
        [result_summary_eid] = result_log.update_result_summary_in_db(
            result_summary=result_summary, eids=[result_summary.eid])
        out_status = None
        try:
            out_cn.connect()
            if not is_dry_run:
                media_ids = out_cn.upload_medias(media_ios)\
                    if self.config.outbound.getboolean("attach_media", "yes")\
                    else []
                out_status = out_cn.update_status(
                    result_summary["status_string"], media_ids=media_ids)
                result_summary["result"] = "Succeed"
            else:
                result_summary["result"] = "Test"
        except TwythonError as twython_ex:
            result_summary["result"] = "Failed"
            result_summary.result_string = "{0}".format(str(twython_ex))
        finally:
            pass
        if not is_dry_run:
            if out_status:
                out_summary = result_log.make_status_summary(
                    "outbound", out_status)
                result_summary.update(out_summary)
        [updated_eid] = result_log.update_result_summary_in_db(
            result_summary=result_summary, eids=[result_summary_eid])
        if result_summary_eid is not updated_eid:
            self.logger.debug("Failed to update log database.")
            return True
        self.logger.info(self.message_to_logger(result_summary=result_summary))
        return False

    def run(self, is_dry_run=True):
        operation_cf = self.config.items["operation"]
        result_log = ResultLog(self.config.items)
        out_cn = self.get_connector("outbound")
        for counter in range(2):
            waiting_result_summaries\
                = result_log.get_result_summaries_by_results(["Waiting"])
            if waiting_result_summaries:
                target = waiting_result_summaries[0]
                media_dicts = target["inbound_medias"]\
                    if "inbound_medias" in target else []
                try:
                    media_ios = []
                    if media_dicts:
                        if not 'in_cn' in locals():
                            in_cn = self.get_connector("inbound")
                            in_cn.connect()
                        media_ios = in_cn.get_media_ios(media_dicts)
                    self.process_one_waiting_status(result_log=result_log,
                                                    result_summary=target,
                                                    media_ios=media_ios,
                                                    out_cn=out_cn, is_dry_run=is_dry_run)
                    return False
                finally:
                    for a_io in media_ios:
                        a_io.io.close()
                return True
            else:
                if counter == 0:
                    in_cn = self.get_connector("inbound")
                    in_cn.connect()
                    trigger_str = self.get_trigger()
                    status_text = StatusText(self.config.outbound)
                    statuses = in_cn.get_statuses_by_hashtag(hashtag=trigger_str, since=self.config.inbound.get("since", ""),
                                                             until=self.config.inbound.get(
                        "until", ""),
                        limit=self.config.inbound.get("limit", ""))
                    eids = self.fill_in_waiting_list(
                        result_log, status_text, statuses, trigger_str)
                    if not eids:
                        return False
        self.logger.warning("Something wrong in waiting list process!")
        return True

    def get_connector(self, dir_str):
        endpoint = self.config.inbound if dir_str == "inbound"\
            else self.config.outbound if dir_str == "outbound"\
            else None
        if endpoint["type"] == "twitter":
            return TwitterConnector(endpoint)
        elif endpoint["type"]:
            return MastodonConnector(endpoint)
        raise DontwiConfigError

    @staticmethod
    def message_to_logger(result_summary):
        keys_to_log = ["result",
                       "processed_at",
                       "inbound",
                       "inbound_status_id",
                       "outbound",
                       "outbound_status_id",
                       "hashtag"]
        values_to_log = [
            result_summary[a_key]
            if a_key in result_summary else "" for a_key in keys_to_log]
        log_str = ("{0[0]} at {0[1]} " + "in:{0[2]},{0[3]} out:{0[4]},{0[5]} " +
                   "tag:{0[6]}").format(values_to_log)
        return log_str
