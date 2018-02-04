# -*- coding: utf-8 -*-
"""Result log manager
"""
from datetime import datetime, timezone
from functools import reduce
from operator import and_, or_

from packaging import version
from tinydb import Query, TinyDB

from .version import __version__


class ResultLog(object):
    """Log DB manager class"""

    def __init__(self, config):
        self.items = config
        self.file_name = self.items["result log"]["db_file"]
        with TinyDB(self.file_name) as db_entity:
            if not db_entity:
                self.__set_info(db_entity)
            else:
                info_table = self.__get_info_table(db_entity)
                app_info = self.__get_info_from_table(info_table)
                version_str = app_info[0]['version'] if app_info else '0'
                if version.parse(version_str) < version.parse('1.0'):
                    self.migrate_to_1_0(db_entity)

    @staticmethod
    def __get_info_table(db_entity):
        info_table = db_entity.table('info')
        return info_table

    @staticmethod
    def __get_info_from_table(info_table):
        app_info = info_table.search(Query().application == 'dontwi')
        return app_info

    def __set_info(self, db_entity):
        info_table = self.__get_info_table(db_entity)
        app_info = self.__get_info_from_table(info_table)
        if not app_info:
            info_table.insert(
                {'application': 'dontwi', 'version': __version__})
        else:
            info_table.update({'version': __version__}, eids=[app_info[0].eid])

    def get_info(self):
        with TinyDB(self.file_name) as db_entity:
            info_table = self.__get_info_table(db_entity)
            app_info = self.__get_info_from_table(info_table)
        return app_info[0]

    def get_record_number(self):
        with TinyDB(self.file_name) as db_entity:
            return len(db_entity)

    def migrate_to_1_0(self, db_entity):
        for element in db_entity:
            if isinstance(element['inbound_status_id'], int):
                element['inbound_status_id'] = str(
                    element['inbound_status_id'])
                db_entity.update(element, eids=[element.eid])
        self.__set_info(db_entity)

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
        with TinyDB(self.file_name) as db_entity:
            summaries = db_entity.search(query)
            return summaries
        return None

    def save_result_summaries(self, result_summaries):
        with TinyDB(self.file_name) as db_entity:
            eids = db_entity.insert_multiple(result_summaries)
            return eids
        return None

    def update_result_summary_in_db(self, result_summary, eids):
        with TinyDB(self.file_name) as db_entity:
            eids2 = db_entity.update(result_summary, eids=eids)
            return eids2
        return True

    def dump_log(self):
        with TinyDB(self.file_name) as db_entity:
            return db_entity.all()

    def remove_summaries_by_eids(self, eids):
        with TinyDB(self.file_name) as db_entity:
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
