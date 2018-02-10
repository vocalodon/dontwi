#!  /usr/bin/python3
# -*- coding: utf-8 -*-
""" Entry point module
"""
import json
from argparse import SUPPRESS, ArgumentParser
from pprint import pprint

from dontwi.config import Config
from dontwi.dontwi import Dontwi
from dontwi.result_log import ResultLog
from dontwi.version import __version__


def show_log_db_summary(conf):
    result_log = ResultLog(conf.items)
    print("dontwi version\t{0}".format(__version__))
    print("log db\t{0}".format(result_log.get_info()))
    print('record number\t{0}'.format(result_log.get_record_number()))
    for result_status in ["Start", "Waiting", "Succeed", "Failed", "Test"]:
        results = result_log.get_result_summaries_by_results([result_status])
        print("{0}\t{1}".format(result_status, len(results)))


def dump_status_strings(conf):
    dontwi = Dontwi(conf)
    in_cn = dontwi.get_connector("inbound")
    in_cn.connect()
    trigger_str = dontwi.get_trigger()
    [since, until, limit] = [
        dontwi.config.inbound.get(option, "")
        for option in ["since", "until", "limit"]]
    statuses, statuses2 = tee(in_cn.get_statuses_by_hashtag(
        hashtag=trigger_str, since=since, until=until, limit=limit))
    status_pr = StatusText(dontwi.config.outbound)
    result_log = ResultLog(dontwi.config.items)
    summaries = dontwi.summaries_to_be_listed(result_log=result_log,
                                              status_pr=status_pr,
                                              statuses=statuses,
                                              trigger_str=trigger_str)
    status_dc = {a_status.get_status_id(): a_status.status["content"]
                 for a_status in statuses2}
    dump_strs = ["{0}\n{1}\n{2}\n[{3}]".format(a_summary["inbound_status_id"], a_summary["status_string"],
                                               a_summary["inbound_status_url"], status_dc[a_summary["inbound_status_id"]])
                 for a_summary in summaries]
    for lint_str in dump_strs:
        print(lint_str)


def dump_log(conf):
    result_log = ResultLog(conf.items)
    print(json.dumps(result_log.dump_log()))


def dump_log_readable(conf):
    result_log = ResultLog(conf.items)
    pprint(result_log.dump_log())


def remove_specified_summaries(conf, results):
    result_log = ResultLog(conf.items)
    summaries = result_log.get_result_summaries_by_results(results)
    eids = [a_summary.eid for a_summary in summaries]
    result_log.remove_summaries_by_eids(eids)


def remove_waiting_result_summaries(conf):
    remove_specified_summaries(conf, ["Waiting"])


def remove_wrong_result_summaries(conf):
    remove_specified_summaries(conf, ["Start", "Failed", "Test"])


def get_secret_and_save(conf):
    dontwi = Dontwi(conf)
    in_cn = dontwi.get_connector("inbound")
    out_cn = dontwi.get_connector("outbound")
    in_cn.connect()
    out_cn.connect()
    conf.save()
    return False


def main():
    ar_prs = ArgumentParser(
        description="A status transporter from Mastodon to Twitter")
    ar_prs.add_argument("--config-file",
                        help="Using CONFIG_FILE instead of default.")
    # ar_prs.add_argument("--init-config",help="Only generate config file when
    # not
    # exists.",action='store_true')
    # ar_prs.add_argument("--init-config",help=argparse.SUPPRESS,action='store_true')
    ar_prs.add_argument("--summary",
                        help="Showing summary of log DB",
                        action="store_true")
    ar_prs.add_argument("--trigger",
                        help="Using TRIGGER instead of trigger in config file")
    ar_prs.add_argument("--since",
                        help="Using SINCE instead of since in config file")
    ar_prs.add_argument("--until",
                        help="Using UNTIL instead of until in config file")
    ar_prs.add_argument("--limit",
                        help="Using LIMIT insted of limit in config file")
    ar_prs.add_argument("--save", help="", action='store_true')
    ar_prs.add_argument("--dry-run",
                        help="Getting last status with the hashtag, " +
                        "but don't update status at outbound service.",
                        action='store_true')
    ar_prs.add_argument("--get-secret",
                        help="Getting client id and others from mastodon instance, " +
                        "and saving these in config file.",
                        action="store_true")
    ar_prs.add_argument("--dump-status-strings",
                        help="Dumping status strings to be marked as 'Waiting' status",
                        action='store_true')
    ar_prs.add_argument("--dump-log",
                        help="Dumping all records in the log database.",
                        action='store_true')
    ar_prs.add_argument("--dump-log-readable",
                        help="Dumping all records in the log database in a human-readable format.",
                        action='store_true')
    ar_prs.add_argument("--remove-waiting",
                        help="Removinng records in 'Waiting' from the database",
                        action='store_true')
    ar_prs.add_argument("--remove-wrong",
                        help="Removinng records in 'Waiting' from the database",
                        action='store_true')
    ar_prs.add_argument("--db-file",
                        help="Using log DB_FILE instead of db_file of [result log] section in config file.")
    ar_prs.add_argument("--ptvsd-secret", help=SUPPRESS)

    args = ar_prs.parse_args()
    if args.ptvsd_secret is not None:
        from socket import gethostname
        from socket import gethostbyname
        import ptvsd
        hostname = gethostname()
        hostname_addr = [hostname, gethostbyname(hostname)]
        for info in hostname_addr:
            print('tcp://{0}@{1}:5678'.format(args.ptvsd_secret, info))
        ptvsd.enable_attach(args.ptvsd_secret)
        ptvsd.wait_for_attach()

    if "help" in args:
        args.print_help()
        exit()

    conf = Config()
    if args.config_file is not None:
        conf.filename = args.config_file
    conf.load()

    if args.db_file is not None:
        conf.items["result log"]["db_file"] = args.db_file
    if args.trigger is not None:
        conf.items["operation"]["trigger"] = args.trigger
    if args.since is not None:
        conf.inbound["since"] = args.since
    if args.until is not None:
        conf.inbound["until"] = args.until
    if args.limit is not None:
        conf.inbound["limit"] = args.limit
    if args.get_secret:
        get_secret_and_save(conf)
        exit()
    if args.save:
        conf.save()
        exit()
    if args.summary:
        show_log_db_summary(conf)
        exit()
    if args.dump_status_strings:
        dump_status_strings(conf)
        exit()
    if args.dump_log:
        dump_log(conf)
        exit()
    if args.dump_log_readable:
        dump_log_readable(conf)
        exit()
    if args.remove_waiting:
        remove_waiting_result_summaries(conf)
        exit()
    if args.remove_wrong:
        remove_wrong_result_summaries(conf)
        exit()
    dontwi = Dontwi(conf)
    dontwi.run(args.dry_run)


if __name__ == "__main__":
    main()
