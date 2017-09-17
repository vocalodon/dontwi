# -*- coding: utf-8 -*-
"""Result log manager
"""
from datetime import datetime, timezone
from functools import reduce
from operator import and_, or_
from tinydb import Query, TinyDB


class ResultLog(object):
    """description of class"""

    def __init__(self, config):
        self.items = config

    def has_result_of_status(self, status, results):
        inbound_str = self.items["operation"]["inbound"]
        query = Query()
        result_q = reduce(or_, [
            query.result == a_result for a_result in results])
        querys = [query.inbound == inbound_str,
                  query.inbound_status_id == status.get_status_id(), result_q]
        combined_query = reduce(and_, querys)
        return self.search_db(combined_query)

    def get_result_summaries_by_status(self, status):
        inbound_str = self.items["operation"]["inbound"]
        query = Query()
        combined_query = (query.inbound == inbound_str) & (
            query.inbound_status_id == status.get_status_id())
        return self.search_db(combined_query)

    def get_result_summaries_by_results(self, results):
        query = Query()
        querys = [query.result == a_result for a_result in results]
        combined_query = reduce(or_, querys)
        return self.search_db(combined_query)

    def search_db(self, query):
        file_name = self.items["result log"]["db_file"]
        with TinyDB(file_name) as db_entity:
            summaries = db_entity.search(query)
            return summaries
        return None

    def make_result_summary(self, inbound_status,
                            outbound_status, status_string, hashtag,
                            result):
        summary = self.make_result_and_others_summary(
            status_string=status_string, hashtag=hashtag, result=result)
        summary.update(self.make_status_summary("inbound",
                                                status=inbound_status))
        summary.update(self.make_status_summary("outbound",
                                                status=outbound_status))
        return summary

    def save_result_summaries(self, result_summaries):
        f_name = self.items["result log"]["db_file"]
        with TinyDB(f_name) as db_entity:
            eids = db_entity.insert_multiple(result_summaries)
            return eids
        return None

    def update_result_summary_in_db(self, result_summary, eids):
        f_name = self.items["result log"]["db_file"]
        with TinyDB(f_name) as db_entity:
            eids2 = db_entity.update(result_summary, eids=eids)
            return eids2
        return True

    def dump_log(self):
        f_name = self.items["result log"]["db_file"]
        with TinyDB(f_name) as db_entity:
            return db_entity.all()

    def remove_summaries_by_eids(self, eids):
        f_name = self.items["result log"]["db_file"]
        with TinyDB(f_name) as db_entity:
            return db_entity.remove(eids=eids)

    def make_status_summary(self, direction, status):
        summary = {
            direction: self.items["operation"][direction],
            direction + "_type": status.get_type(),
            direction + "_status_id": status.get_status_id(),
            direction + "_status_url": status.get_status_url()
        }
        if direction == "inbound":
            summary[direction + "_medias"] = status.get_medias()
        return summary

    @staticmethod
    def make_result_and_others_summary(status_string, hashtag, result):
        summary = {"result": result,
                   "hashtag": hashtag,
                   "status_string": status_string}
        summary.update(ResultLog.get_processed_at_dict())
        return summary

    @staticmethod
    def get_processed_at_dict():
        return {"processed_at": datetime.now(timezone.utc).isoformat()}
