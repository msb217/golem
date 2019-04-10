import json
import os
from typing import Optional

from apps.transcoding.ffmpeg.utils import StreamOperator


class UnsupportedCodecType(Exception):
    pass


class FfprobeFormatReport:

    ATTRS_TO_CHECK = [
        'stream_types',
        'duration',
        'start_time',
    ]

    def __init__(self, raw_report: dict):
        self._raw_report = raw_report
        self._stream_reports = self._create_stream_reports(raw_report)

    @classmethod
    def _create_stream_report(cls, raw_stream_report):
        codec_type_to_report_class = {
            'video':    FfprobeVideoStreamReport,
            'audio':    FfprobeAudioStreamReport,
            'subtitle': FfprobeSubtitleStreamReport,
            'data':     FfprobeDataStreamReport,
        }

        codec_type = raw_stream_report['codec_type']
        if codec_type not in codec_type_to_report_class:
            raise UnsupportedCodecType(
                f"Unexpected codec type: {codec_type}. "
                f"A new stream report class is needed to handle it."
            )

        report_class = codec_type_to_report_class[codec_type]
        return report_class(raw_stream_report)

    @classmethod
    def _create_stream_reports(cls, raw_report):
        if 'streams' not in raw_report:
            return []

        return [
            cls._create_stream_report(raw_stream_report)
            for raw_stream_report in raw_report['streams']
        ]

    @property
    def stream_reports(self):
        return self._stream_reports

    @property
    def stream_types(self):
        streams = self._raw_report['streams']
        streams_dict: Dict[str, int] = {}

        for stream in streams:
            codec_type = stream['codec_type']
            if codec_type in streams_dict:
                streams_dict[codec_type] = streams_dict[codec_type] + 1
            else:
                streams_dict.update({codec_type: 1})
        return streams_dict

    @property
    def duration(self):
        value = self._raw_report.get('format', {}).get('duration', None)
        return FuzzyDuration(value, 10)

    @property
    def start_time(self):
        value = self._raw_report.get('format', {}).get('start_time', None)
        return FuzzyDuration(value, 0)

    def diff(self, format_report: dict, overrides: Optional[dict] = None):
        if overrides is None:
            overrides = {}

        differences = list()
        for attr in self.ATTRS_TO_CHECK:
            original_value = getattr(self, attr)
            modified_value = getattr(format_report, attr)

            if 'streams' in overrides and attr in overrides['streams']:
                modified_value = overrides['streams'][attr]

            if 'format' in overrides and attr in overrides['format']:
                modified_value = overrides['format'][attr]

            if modified_value != original_value:
                diff_dict = {
                    'location': 'format',
                    'attribute': attr,
                    'original value': original_value,
                    'modified value': modified_value,
                }
                differences.append(diff_dict)
        return differences

    def __eq__(self, other):
        return len(self.diff(other, {})) == 0

    @classmethod
    def build(cls, *video_paths: str) -> list:
        dirs_and_basenames: dict = {}
        for path in video_paths:
            dirname, basename = os.path.split(path)
            dirs_and_basenames[dirname] = (
                dirs_and_basenames.get(dirname, []) +
                [basename]
            )

        list_of_reports = []
        stream_operator = StreamOperator()

        for key in dirs_and_basenames:
            metadata = stream_operator.get_metadata(
                dirs_and_basenames[key],
                key
            )
            for path in metadata['data']:
                with open(path) as metadata_file:
                    list_of_reports.append(FfprobeFormatReport(
                        json.loads(metadata_file.read())
                    ))
        return list_of_reports

class FuzzyDuration:
    def __init__(self, duration, tolerance):
        self._duration = duration
        self._tolerance = tolerance

    @property
    def duration(self):
        return self._duration

    def __eq__(self, other):
        duration1 = float(self.duration)
        duration2 = float(other.duration)

        # We treat both fuzzy values as closed intervals:
        # [value - tolerance, value + tolerance]
        # If the intervals overlap at at least one point, we have a match.
        return abs(duration1 - duration2) <= self._tolerance + other._tolerance

    def __str__(self):
        if self._tolerance == 0:
            return f'{self._duration}'

        return f'{self._duration}+/-{self._tolerance}'

    def __repr__(self):
        return f'FuzzyDuration({self._duration}, {self._tolerance})'


class FfprobeStreamReport:
    ATTRS_TO_CHECK = [
        'codec_type',
        'codec_name',
    ]

    def __init__(self, raw_report: dict):
        self._raw_report = raw_report

    @property
    def codec_type(self):
        return self._raw_report.get('codec_type', None)

    @property
    def codec_name(self):
        return self._raw_report.get('codec_name', None)

    def __eq__(self, other):
        return len(self.diff(other, {})) == 0


class FfprobeVideoStreamReport(FfprobeStreamReport):
    ATTRS_TO_CHECK = FfprobeStreamReport.ATTRS_TO_CHECK + [
        'start_time',
        'duration',
        'resolution',
    ]

    def __init__(self, raw_report: dict):
        assert raw_report['codec_type'] == 'video'
        super().__init__(raw_report)

    @property
    def start_time(self):
        return FuzzyDuration(self._raw_report['start_time'], 0)

    @property
    def duration(self):
        if 'duration' not in self._raw_report:
            return None

        return FuzzyDuration(self._raw_report['duration'], 0)

    @property
    def resolution(self):
        return (
            self._raw_report.get('resolution', None),
            self._raw_report.get('width', None),
            self._raw_report.get('height', None),
        )

    def diff(self,
             format_report: dict,
             overrides: Optional[dict] = None) -> list:

        if overrides is None:
            overrides = {}

        differences = list()
        for attr in self.ATTRS_TO_CHECK:
            original_value = getattr(self, attr)
            modified_value = getattr(format_report, attr)

            if modified_value != original_value:
                diff_dict = {
                    'location': 'video',
                    'attribute': attr,
                    'original value': original_value,
                    'modified value': modified_value,
                }
                differences.append(diff_dict)
        return differences


class FfprobeAudioStreamReport(FfprobeStreamReport):
    def __init__(self, raw_report: dict):
        assert raw_report['codec_type'] == 'audio'
        super().__init__(raw_report)


class FfprobeSubtitleStreamReport(FfprobeStreamReport):
    def __init__(self, raw_report: dict):
        assert raw_report['codec_type'] == 'subtitle'
        super().__init__(raw_report)


class FfprobeDataStreamReport(FfprobeStreamReport):
    def __init__(self, raw_report: dict):
        assert raw_report['codec_type'] == 'data'
        super().__init__(raw_report)