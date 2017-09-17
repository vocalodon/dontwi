# -*- coding: utf-8 -*-
""" Processing of attached media
"""
from abc import ABCMeta, abstractmethod
from os import remove
from os.path import exists
from exception import DontwiNotImplementedError
from magic import Magic
from io import BytesIO, SEEK_SET, SEEK_END
from exception import DontwiMediaError
from math import sqrt
#from PIL import Image
#from ffmpeg import input, output, filter_, run
#from ffprobe3 import FFProbe


class IMedia(metaclass=ABCMeta):
    """Interface for processing of attached media"""

    @abstractmethod
    def __init__(self):
        self.magic = Magic(mime=True)

    @abstractmethod
    def get_adapted_image(self, image_io):
        raise DontwiNotImplementedError

    @abstractmethod
    def get_adapted_video(self, video_io):
        raise DontwiNotImplementedError

    def get_mime(self, media_io):
        if hasattr(media_io, "getvalue"):
            buffer = media_io.getvalue()
        elif hasattr(media_io, "seekable") and media_io.seekable():
            buffer = media_io.read(1024)
            media_io.seek(SEEK_SET)
        else:
            raise DontwiMediaError
        return self.magic.from_buffer(buffer)

    @staticmethod
    def get_media_size(media_io):
        if hasattr(media_io, "getvalue"):
            size = len(media_io.getvalue())
        elif hasattr(media_io, "seekable") and media_io.seekable():
            media_io.seek(0, SEEK_END)
            size = media_io.tell()
            media_io.seek(SEEK_SET)
        else:
            raise DontwiMediaError
        return size


class TwitterMedia(IMedia):
    """Processing of attached media for twitter upload"""

    def __init__(self):
        super().__init__()

    def get_adapted_image(self, image_io):
        """Image size <= 5 MB, animated GIF size <= 15 MB"""
        file_size = self.get_media_size(image_io)
        image = Image.open(image_io)
        limit = 1048576 * 5
        if file_size > limit:
            scale = sqrt(file_size / limit)
            resize = tuple(map(lambda val: int(scale * val), size))
        mime = self.get_mime(image_io)
        return image_io, mime

    def get_adapted_video(self, video_io):
        temp_in_name = "temp_in"
        temp_out_name = "temp_out.mp4"
        for a_name in [temp_in_name, temp_out_name]:
            if exists(a_name):
                remove(a_name)

        with open(temp_in_name, "bw") as temp_in:
            temp_in.write(video_io.read())

        frame_size = FFProbe(temp_in_name).streams[0].frame_size()
        limit_frame_size = (1280, 1024)
        if frame_size[0] > limit_frame_size[0] or frame_size[1] > limit_frame_size[1]:
            scale = min(limit_frame_size[0] / frame_size[0],
                        limit_frame_size[1] / frame_size[1])

            def resize_func(value): return int(scale * value)
            (input(temp_in_name)
                .filter_("scale", "w={0[0]}:h={0[1]}".format(list(map(resize_func, frame_size))))
                .output(temp_out_name)
                .run())
            temp_out = open(temp_out_name, "br")
            mime = self.get_mime(temp_out)
            return temp_out, mime
        else:
            mime = self.get_mime(video_io)
            return video_io, mime
