import logging
from enum import Enum
from typing import Type

from golem.core.common import HandleValueError

logger = logging.getLogger(__name__)


def not_valid_json(exception_type: Type[Exception], path: str):
    msg = 'File {} is not valid JSON'.format(path)
    logger.warning(msg)
    raise exception_type(msg)


def file_io_error(path: str):
    msg = 'I/O error occurred during access to file {}'.format(path)
    logger.warning(msg)
    raise TranscodingException(msg)


def unsupported(name: str):
    logger.warning('%s is not supported', name)
    raise TranscodingTaskBuilderException('{} is not supported'.format(name))


class VideoCodec(Enum):
    AV1 = 'av1'           # Alliance for Open Media AV1
    FLV1 = 'flv1'         # FLV / Sorenson Spark / Sorenson H.263 (Flash Video)
    H_263 = 'h263'        # H.263 / H.263-1996,
                          # H.263+ / H.263-1998 / H.263 version 2
    H_264 = 'h264'        # H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10
    H_265 = 'h265'
    HEVC = 'hevc'         # H.265 / HEVC (High Efficiency Video Coding)
    MJPEG = 'mjpeg'       # Motion JPEG
    MPEG_1 = 'mpeg1video' # MPEG-1 video
    MPEG_2 = 'mpeg2video' # MPEG-2 video
    MPEG_4 = 'mpeg4'      # MPEG-4 part 2
    THEORA = 'theora'     # Theora
    VP8 = 'vp8'           # On2 VP8
    VP9 = 'vp9'           # Google VP9
    WMV1 = 'wmv1'         # Windows Media Video 7
    WMV2 = 'wmv2'         # Windows Media Video 8

    @staticmethod
    @HandleValueError(unsupported)
    def from_name(name: str) -> 'VideoCodec':
        return VideoCodec(name)


class AudioCodec(Enum):
    AAC = 'aac'        # AAC (Advanced Audio Coding)
    AC3 = 'ac3'        # ATSC A/52A (AC-3)
    AMR_NB = 'amr_nb'  # AMR-NB (Adaptive Multi-Rate NarrowBand)
    MP2 = 'mp2'        # MP2 (MPEG audio layer 2)
    MP3 = 'mp3'        # MP3 (MPEG audio layer 3)
    OPUS = 'opus'      # Opus (Opus Interactive Audio Codec)
    PCM_U8 = 'pcm_u8'  # PCM unsigned 8-bit
    WMAV2 = 'wmav2'    # Windows Media Audio 2
    VORBIS = 'vorbis'  # Vorbis

    @staticmethod
    @HandleValueError(unsupported)
    def from_name(name: str) -> 'AudioCodec':
        return AudioCodec(name)


class Container(Enum):
    """ Containers that can be used as transcoding target. Values are muxer
        names used by ffmpeg (see `ffmpeg -muxers` for full list) rather than
        file extensions and can be used directly with the `-f` option.

        Note that:
        1. A container format corresponds to a muxer/demuxer pair in ffmpeg.
           Muxer can write it and demuxer can read it.
        2. There is no 1:1 correspondence between muxers and demuxers. Often
           a demuxer can read more than one format and thus can be paired with
           multiple muxers (e.g. files produced by both `mp4` and `mov` muxers
           can be read by the `mov,mp4,m4a,3gp,3g2,mj2` demuxer).
           There are also many formats for which ffmpeg supports only encoding
           or only decoding so one of the pair is missing.
        3. Ideally a container as we understand it should be more general than
           a muxer. E.g. in theory ffmpeg could provide two different muxers
           capable of producing the same format. We could also switch to a
           different program/library that does things differently. In practice
           it's hard to achieve since we're completely relying on ffmpeg here.
    """

    ASF = 'asf'           # ASF (Advanced / Active Streaming Format);
                          # .asf and .wmv extension
    FLV = 'flv'           # FLV (Flash Video)
    IPOD = 'ipod'         # iPod H.264 MP4 (MPEG-4 Part 14); .m4v extension
    MOV = 'mov'           # QuickTime / MOV
    MP4 = 'mp4'           # MP4 (MPEG-4 Part 14)
    MPEG = 'mpeg'         # MPEG-1 Systems / MPEG program stream
    MPEGTS = 'mpegts'     # MPEG-TS (MPEG-2 Transport Stream)
    AVI = 'avi'           # AVI (Audio Video Interleaved)
    MATROSKA = 'matroska' # Matroska
    OGV = 'ogv'           # Ogg Video
    SVCD = 'svcd'         # MPEG-2 PS (SVCD); .vob extension
    WEBM = 'webm'         # WebM
    X_3GP = '3gp'         # 3GP (3GPP file format)

    @staticmethod
    @HandleValueError(unsupported)
    def from_name(name: str) -> 'Container':
        return Container(name.lower())

    def get_supported_video_codecs(self):
        return CONTAINER_SUPPORTED_CODECS[self][0]

    def get_supported_audio_codecs(self):
        return CONTAINER_SUPPORTED_CODECS[self][1]


class Demuxer(Enum):
    ASF = 'asf'                       # ASF (Advanced / Active Streaming Format)
    FLV = 'flv'                       # FLV (Flash Video)
    MOV_MP4_M4A_3GP_3G2_MJ2 = 'mov,mp4,m4a,3gp,3g2,mj2'   # QuickTime / MOV
    MPEG = 'mpeg'                     # MPEG-1 Systems / MPEG program stream
    MPEGTS = 'mpegts'                 # MPEG-TS (MPEG-2 Transport Stream)
    AVI = 'avi'                       # AVI (Audio Video Interleaved)
    MATROSKA_WEBM = 'matroska,webm'   # Matroska / WebM
    OGG = 'ogg'                       # Ogg


CONTAINER_TO_DEMUXER = {
    Container.ASF: Demuxer.ASF,
    Container.FLV: Demuxer.FLV,
    Container.IPOD: Demuxer.MOV_MP4_M4A_3GP_3G2_MJ2,
    Container.MOV: Demuxer.MOV_MP4_M4A_3GP_3G2_MJ2,
    Container.MP4: Demuxer.MOV_MP4_M4A_3GP_3G2_MJ2,
    Container.MPEG: Demuxer.MPEG,
    Container.MPEGTS: Demuxer.MPEGTS,
    Container.AVI: Demuxer.AVI,
    Container.MATROSKA: Demuxer.MATROSKA_WEBM,
    Container.OGV: Demuxer.OGG,
    Container.SVCD: Demuxer.MPEG,
    Container.WEBM: Demuxer.MATROSKA_WEBM,
    Container.X_3GP: Demuxer.MOV_MP4_M4A_3GP_3G2_MJ2,
}
assert set(CONTAINER_TO_DEMUXER) == set(Container)
assert set(CONTAINER_TO_DEMUXER.values()).issubset(set(Demuxer))


ALL_SUPPORTED_CODECS = ([c for c in VideoCodec], [c for c in AudioCodec])
CONTAINER_SUPPORTED_CODECS = {
    Container.AVI: (
        [
            VideoCodec.FLV1,
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA,
            VideoCodec.VP8,
            VideoCodec.VP9,
            VideoCodec.WMV1,
            VideoCodec.WMV2,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP3,
        ],
    ),
    Container.MATROSKA: (
        [
            VideoCodec.FLV1,
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA,
            VideoCodec.VP8,
            VideoCodec.VP9,
            VideoCodec.WMV1,
            VideoCodec.WMV2,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP3,
            AudioCodec.VORBIS,
        ],
    ),
    Container.MP4: (
        [
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.VP9,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP3,
        ]
    ),

    Container.ASF: (
        [
            VideoCodec.FLV1,
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            #VideoCodec.HEVC,  # ffmpeg complains about incorrect codec params
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA,
            VideoCodec.VP8,
            VideoCodec.VP9,
            VideoCodec.WMV1,
            VideoCodec.WMV2,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP3,
            AudioCodec.WMAV2,
        ],
    ),
    Container.FLV: (
        [
            VideoCodec.FLV1,
            VideoCodec.H_264,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP3,
        ],
    ),
    Container.IPOD: (
        [
            VideoCodec.H_264,
            VideoCodec.MPEG_4,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.AC3,
            AudioCodec.MP3,
        ],
    ),
    Container.MOV: (
        [
            VideoCodec.FLV1,   # ffmpeg warns that the file may be unplayable
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA, # ffmpeg warns that the file may be unplayable
            VideoCodec.WMV1,   # ffmpeg warns that the file may be unplayable
            VideoCodec.WMV2,   # ffmpeg warns that the file may be unplayable
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP3,
            AudioCodec.PCM_U8,
        ],
    ),
    Container.MPEG: (
        [
            VideoCodec.FLV1,
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA,
            VideoCodec.VP8,
            VideoCodec.VP9,
            VideoCodec.WMV1,
            VideoCodec.WMV2,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP2,
            AudioCodec.MP3,
        ],
    ),
    Container.MPEGTS: (
        [
            VideoCodec.FLV1,
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA,
            VideoCodec.VP8,
            VideoCodec.VP9,
            VideoCodec.WMV1,
            VideoCodec.WMV2,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.AC3,
            AudioCodec.MP3,
        ],
    ),
    Container.OGV: (
        [
            VideoCodec.THEORA,
            VideoCodec.VP8,
        ],
        [
            AudioCodec.OPUS,
            AudioCodec.VORBIS,
        ],
    ),
    Container.SVCD: (
        [
            VideoCodec.FLV1,
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.HEVC,
            VideoCodec.MJPEG,
            VideoCodec.MPEG_1,
            VideoCodec.MPEG_2,
            VideoCodec.MPEG_4,
            VideoCodec.THEORA,
            VideoCodec.VP8,
            VideoCodec.VP9,
            VideoCodec.WMV1,
            VideoCodec.WMV2,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.MP2,
            AudioCodec.MP3,
        ],
    ),
    Container.WEBM: (
        [
            VideoCodec.VP8,
            VideoCodec.VP9,
        ],
        [
            AudioCodec.OPUS,
            AudioCodec.VORBIS,
        ],
    ),
    Container.X_3GP: (
        [
            #VideoCodec.H_263, # Only some resolutions are supported
            VideoCodec.H_264,
            VideoCodec.MPEG_4,
        ],
        [
            AudioCodec.AAC,
            AudioCodec.AMR_NB,
        ],
    ),
}

# Make sure that the definitions above satisfy our assumptions:
assert set(CONTAINER_SUPPORTED_CODECS) == set(Container)
assert all(
    set(CONTAINER_SUPPORTED_CODECS[c][0]).issubset(set(VideoCodec))
    for c in Container)
assert all(
    set(CONTAINER_SUPPORTED_CODECS[c][1]).issubset(set(AudioCodec))
    for c in Container)


def is_type_of(t: Type):
    def f(obj):
        return isinstance(obj, t)

    return f


class ffmpegException(Exception):
    pass


class ffmpegExtractSplitError(ffmpegException):
    pass


class ffmpegTranscodingError(ffmpegException):
    pass


class ffmpegMergeReplaceError(ffmpegException):
    pass


class TranscodingException(Exception):
    pass


class TranscodingTaskBuilderException(Exception):
    pass


class VideoCodecNotSupportedByContainer(TranscodingTaskBuilderException):
    pass


class AudioCodecNotSupportedByContainer(TranscodingTaskBuilderException):
    pass
