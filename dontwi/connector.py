# -*- coding: utf-8 -*-
"""Management of connections to twitter and mastodon instance
"""
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from io import BytesIO
from operator import ge, le

import requests
from dateutil.parser import parse
from magic import Magic
from mastodon import Mastodon
from twython import Twython

from .exception import DontwiNotImplementedError
from .media import TwitterMedia
from .status_text import StatusText


class IConnector(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def connect(self, do_login=False):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_statuses_by_hashtag(self, hashtag, since, until, limit):
        raise DontwiNotImplementedError

    @abstractmethod
    def update_status(self, status_string, media_ids):
        raise DontwiNotImplementedError

    @abstractmethod
    def upload_medias(self, media_ios):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_media_ios(self, media_dicts):
        raise DontwiNotImplementedError

    MediaIo = namedtuple("MediaIo", ["type", "io"])


class MastodonConnector(IConnector):

    def __init__(self, config):
        super().__init__(config)
        self.mastodon = None

    def register_to_mastodon(self):
        res = Mastodon.create_app(client_name=self.config["client_name"],
                                  api_base_url=self.config["api_base_url"])
        self.config["client_id"] = res[0]
        self.config["client_secret"] = res[1]
        return False

    def connect(self, do_login=False):
        if "client_id" is not self.config \
                or "client_secret" is not self.config:
            if self.register_to_mastodon():
                return True
        if do_login and "access_token" is not self.config:
            self.mastodon = Mastodon(client_id=self.config["client_id"],
                                     client_secret=self.config["client_secret"],
                                     api_base_url=self.config["api_base_url"])
            ac_tk = self.mastodon.log_in(username=self.config["username"],
                                         password=self.config["password"])
            if not isinstance(ac_tk, str) or not ac_tk == "":
                return True
            self.config["access_token"] = ac_tk
        else:
            self.mastodon = Mastodon(client_id=self.config["client_id"],
                                     client_secret=self.config["client_secret"],
                                     api_base_url=self.config["api_base_url"])
        return False

    @staticmethod
    def get_since_id_and_condition_func(since, operator=ge):
        if since.startswith("id:"):
            since_id = int(since.rpartition(":")[-1])

            def condition(status):
                return True
        else:
            since_id = None

            def condition(status):
                if isinstance(status["created_at"], str):
                    created_at = parse(status["created_at"])
                else:
                    created_at = status["created_at"]
                if since != "":
                    return operator(created_at, parse(since))
                else:
                    return True

        return since_id, condition

    def __get_timeline_statuses_by_hashtag(
            self, hashtag, since_id, max_id, limit):
        statuses = []
        for a_hashtag in [hashtag, StatusText.federation_hashtag]:
            statuses += self.mastodon.timeline_hashtag(
                hashtag=a_hashtag, local=True, max_id=max_id, since_id=since_id, limit=limit)
        statuses.sort(key=lambda status: status["id"], reverse=True)
        return statuses

    def get_statuses_by_hashtag(self, hashtag, since, until="", limit=""):
        since_id, since_cond = self.get_since_id_and_condition_func(since, ge)
        max_id, until_cond = self.get_since_id_and_condition_func(until, le)
        _limit = limit if limit != "" else None
        searched_statuses = self.__get_timeline_statuses_by_hashtag(
            hashtag=hashtag, since_id=since_id, max_id=max_id, limit=_limit)
        for a_status in reversed(searched_statuses):
            if a_status["visibility"] == "public"\
                    and not a_status["mentions"]\
                    and not a_status["in_reply_to_id"]\
                    and since_cond(a_status) and until_cond(a_status):
                yield TootStatus(a_status)

    def update_status(self, status_string, media_ids):
        return super().update_status(status_string, media_ids)

    def upload_medias(self, media_ios):
        return super().upload_medias(media_ios)

    def get_media_ios(self, media_dicts):
        for a_media_dict in media_dicts:
            response = requests.get(a_media_dict["url"])
            yield self.MediaIo(type=a_media_dict["type"], io=BytesIO(response.content))


class TwitterConnector(IConnector):

    def __init__(self, config):
        super().__init__(config)
        self.twitter = None
        self.magic = Magic(mime=True)

    def connect(self, do_login=False):
        app_key = self.config["app_key"]
        app_secet = self.config["app_secret"]
        oauth_token = self.config["oauth_token"]
        oauth_token_secret = self.config["oauth_token_secret"]
        self.twitter = Twython(app_key,
                               app_secet,
                               oauth_token,
                               oauth_token_secret)
        return None

    def get_statuses_by_hashtag(self, hashtag, since, until, limit):
        return super().get_statuses_by_hashtag(hashtag, since, until, limit)

    def update_status(self, status_string, media_ids, in_reply_to_status_id=None):
        if in_reply_to_status_id:
            return TweetStatus(self.twitter.update_status(
                status=status_string, media_ids=media_ids, in_reply_to_status_id=in_reply_to_status_id))
        else:
            return TweetStatus(self.twitter.update_status(
                status=status_string, media_ids=media_ids))

    def upload_medias(self, media_ios):
        responses = []
        media = TwitterMedia()
        for a_io in media_ios:
            try:
                if a_io.type == "image":
                    #media_io, mime = media.get_adapted_image(image_io=a_io.io)
                    media_io, mime = (a_io.io, media.get_mime(a_io.io))
                    responses.append(self.twitter.upload_media(media=a_io.io))
                elif a_io.type == "video" or a_io.type == "gifv":
                    #media_io, mime = media.get_adapted_video(video_io=a_io.io)
                    media_io, mime = (a_io.io, media.get_mime(a_io.io))
                    # responses.append(self.twitter.upload_video(media_io,
                    # media_type=mime))
            finally:
                media_io.close()
        media_ids = [a_response["media_id"] for a_response in responses]
        return media_ids

    def get_media_ios(self, media_dicts):
        return super().get_media_ios(media_dicts)


class IStatus(metaclass=ABCMeta):
    def __init__(self, status_dict):
        self._status = status_dict

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status_dict):
        self._status = status_dict

    @property
    def type(self):
        return self.get_type()

    @property
    def dict(self):
        return {"type": self.type, "status": self.status}

    @abstractmethod
    def get_type(self):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_status_id(self):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_user_url(self):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_user_account(self):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_status_url(self):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_medias(self):
        raise DontwiNotImplementedError


class TweetStatus(IStatus):

    def get_type(self):
        return "twitter"

    def get_status_id(self):
        return self._status["id_str"]

    def get_user_url(self):
        return super().get_user_url()

    def get_user_account(self):
        return super().get_user_account()

    def get_status_url(self):
        return "https://twitter.com/{0}/status/{1}".format(
            self._status["user"]["screen_name"], self._status["id_str"])

    def get_medias(self):
        return super().get_medias()


class TootStatus(IStatus):

    def _status_setter(self, status_dict):
        if "_pagination_prev" is status_dict:
            del status_dict["_pagination_prev"]
        self._status = status_dict

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status_dict):
        self._status_setter(status_dict)

    def get_type(self):
        return "mastodon"

    def get_status_id(self):
        return str(self._status["id"])

    def get_user_id(self):
        return self._status["account"]["id"]

    def get_user_url(self):
        return self._status["account"]["url"]

    def get_user_account(self):
        [prefix, null_str, domain,
            username] = self._status["account"]["url"].rsplit("/", 3)
        return "{0}@{1}".format(username, domain)

    def get_status_url(self):
        return self._status["url"]

    def get_medias(self):
        return self._status["media_attachments"]\
            if "media_attachments" in self._status else []
