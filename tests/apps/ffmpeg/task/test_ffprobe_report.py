import copy
from typing import Any, List
from unittest import TestCase

import pytest
from parameterized import parameterized

from golem.testutils import TempDirFixture
from tests.apps.ffmpeg.task.ffprobe_report import FfprobeFormatReport, \
    FuzzyDuration, FuzzyInt, FfprobeAudioAndVideoStreamReport, \
    FfprobeVideoStreamReport, FfprobeAudioStreamReport, FfprobeStreamReport
from tests.apps.ffmpeg.task.ffprobe_report_sample_reports import \
    RAW_REPORT_ORIGINAL, RAW_REPORT_WITH_MPEG4
from tests.apps.ffmpeg.task.test_ffmpegtask import PrepareDockerTaskMixin


class WrongRawReportFormatException(TypeError):
    pass


class TestFfprobeFormatReport(TestCase):
    @staticmethod
    def _change_value_in_dict(dict_path: List[tuple],
                              new_value: Any,
                              raw_report_to_modify: dict) -> dict:

        for fields in dict_path:
            sub_dict = raw_report_to_modify
            for field in fields:
                if field == fields[-1]:
                    sub_dict[field] = new_value
                else:
                    if isinstance(sub_dict, dict):
                        sub_dict = sub_dict.get(field)  # type: ignore
                    elif isinstance(sub_dict, list):
                        sub_dict = sub_dict[field]
                    else:
                        raise WrongRawReportFormatException(
                            f'Raw report should contain only nested lists '
                            f'or dictionaries, not {type(sub_dict)}'
                        )
        return raw_report_to_modify

    def test_reports_with_shuffled_streams_should_be_compared_as_equal(self):
        report_original = FfprobeFormatReport(RAW_REPORT_ORIGINAL)
        raw_report_shuffled = copy.deepcopy(RAW_REPORT_ORIGINAL)

        for stream in raw_report_shuffled['streams']:
            if stream['index'] % 2 == 0:
                stream['index'] = stream['index'] + 1
            else:
                stream['index'] = stream['index'] - 1

        sorted(raw_report_shuffled['streams'], key=lambda i: i['index'])
        assert raw_report_shuffled != RAW_REPORT_ORIGINAL
        report_shuffled = FfprobeFormatReport(raw_report_shuffled)

        self.assertEqual(report_original, report_shuffled)

    def test_missing_modified_stream_should_be_reported(self):
        raw_report_original = copy.deepcopy(RAW_REPORT_ORIGINAL)
        del raw_report_original['streams'][2]
        report_original = FfprobeFormatReport(raw_report_original)

        raw_report_modified = copy.deepcopy(RAW_REPORT_ORIGINAL)
        del raw_report_modified['streams'][10]
        del raw_report_modified['streams'][9]
        report_modified = FfprobeFormatReport(raw_report_modified)

        diff = report_modified.diff(report_original)

        expected_diff = [
            {
                'location': 'format',
                'attribute': 'stream_types',
                'original_value':
                    {
                        'video': 1,
                        'audio': 2,
                        'subtitle': 6
                    },
                'modified_value':
                    {
                        'video': 1,
                        'audio': 2,
                        'subtitle': 7
                    },
                'reason': 'Different attribute values'
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'eng',
                'modified_value': 'hun',
                'reason': 'Different attribute values',
                'original_stream_index': 2,
                'modified_stream_index': 3
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'hun',
                'modified_value': 'ger',
                'reason': 'Different attribute values',
                'original_stream_index': 3,
                'modified_stream_index': 4
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'ger',
                'modified_value': 'fre',
                'reason': 'Different attribute values',
                'original_stream_index': 4,
                'modified_stream_index': 5
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'fre',
                'modified_value': 'spa',
                'reason': 'Different attribute values',
                'original_stream_index': 5,
                'modified_stream_index': 6
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'spa',
                'modified_value': 'ita',
                'reason': 'Different attribute values',
                'original_stream_index': 6,
                'modified_stream_index': 7
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'ita',
                'modified_value': 'jpn',
                'reason': 'Different attribute values',
                'original_stream_index': 7,
                'modified_stream_index': 9
            },
            {
                'location': 'subtitle',
                'original_stream_index': None,
                'modified_stream_index': 10,
                'reason': 'No matching stream'}
        ]
        self.assertCountEqual(diff, expected_diff)

    def test_missing_original_stream_should_be_reported(self):
        raw_report_original = copy.deepcopy(RAW_REPORT_ORIGINAL)
        del raw_report_original['streams'][10]
        del raw_report_original['streams'][9]
        report_original = FfprobeFormatReport(raw_report_original)

        raw_report_modified = copy.deepcopy(RAW_REPORT_ORIGINAL)
        del raw_report_modified['streams'][2]
        report_modified = FfprobeFormatReport(raw_report_modified)

        diff = (report_modified.diff(report_original))
        expected_diff = [
            {
                'location': 'format',
                'attribute': 'stream_types',
                'original_value': {
                    'audio': 2,
                    'video': 1,
                    'subtitle': 7
                },
                'modified_value': {
                    'video': 1,
                    'audio': 2,
                    'subtitle': 6,
                },
                'reason': 'Different attribute values',
            },
            {
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'jpn',
                'modified_value': 'eng',
                'reason': 'Different attribute values',
                'original_stream_index': 9,
                'modified_stream_index': 2,

            },
            {
                'location': 'subtitle',
                'original_stream_index': 6,
                'modified_stream_index': None,
                'reason': 'No matching stream'
            },
        ]
        self.assertCountEqual(diff, expected_diff)

    def test_report_should_have_video_fields_with_proper_values(self):
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['width'] == 560
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['height'] == 320
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['pix_fmt'] == 'yuv420p'
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['r_frame_rate'] == '30/1'

        report = FfprobeFormatReport(RAW_REPORT_WITH_MPEG4)

        self.assertEqual(report.stream_reports[0].resolution, (560, 320))
        self.assertEqual(report.stream_reports[0].pixel_format, 'yuv420p')
        self.assertEqual(report.stream_reports[0].frame_rate, 30)

    def test_all_video_properties_are_tested(self):
        video_attributes = [
            x
            for x in FfprobeVideoStreamReport.ATTRIBUTES_TO_COMPARE
            if x not in FfprobeAudioAndVideoStreamReport.ATTRIBUTES_TO_COMPARE
        ]
        self.assertCountEqual(
            video_attributes,
            ['resolution', 'pixel_format', 'frame_rate']
        )

    def test_report_should_have_audio_fields_with_proper_values(self):
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['sample_rate'] == '48000'
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['channels'] == 1
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['channel_layout'] == 'mono'
        assert not hasattr(RAW_REPORT_WITH_MPEG4['streams'][1], 'sample_format')

        report = FfprobeFormatReport(RAW_REPORT_WITH_MPEG4)

        self.assertEqual(report.stream_reports[1].sample_rate, 48000)
        self.assertEqual(report.stream_reports[1].sample_format, None)
        self.assertEqual(report.stream_reports[1].channel_count, 1)
        self.assertEqual(report.stream_reports[1].channel_layout, 'mono')

    def test_all_audio_properties_are_tested(self):
        audio_attributes = [
            x
            for x in FfprobeAudioStreamReport.ATTRIBUTES_TO_COMPARE
            if x not in FfprobeAudioAndVideoStreamReport.ATTRIBUTES_TO_COMPARE
        ]
        self.assertCountEqual(
            audio_attributes,
            ['sample_rate', 'sample_format', 'channel_count', 'channel_layout']
        )

    def test_report_should_have_audio_and_video_fields_with_proper_values(self):
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['duration'] == '5.566667'
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['bit_rate'] == '499524'
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['nb_frames'] == '167'

        assert RAW_REPORT_WITH_MPEG4['streams'][1]['duration'] == '5.640000'
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['bit_rate'] == '64275'
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['nb_frames'] == '235'

        report = FfprobeFormatReport(RAW_REPORT_WITH_MPEG4)

        self.assertEqual(report.stream_reports[0].duration.duration, 5.566667)
        self.assertEqual(report.stream_reports[0].bitrate.value, 499524)
        self.assertEqual(report.stream_reports[0].frame_count, 167)

        self.assertEqual(report.stream_reports[1].duration.duration, 5.64)
        self.assertEqual(report.stream_reports[1].bitrate.value, 64275)
        self.assertEqual(report.stream_reports[1].frame_count, 235)

    def test_all_audio_and_video_properties_are_tested(self):
        audio_and_video_attributes = [
            x
            for x in FfprobeAudioAndVideoStreamReport.ATTRIBUTES_TO_COMPARE
            if x not in FfprobeStreamReport.ATTRIBUTES_TO_COMPARE
        ]
        self.assertCountEqual(
            audio_and_video_attributes,
            ['duration', 'bitrate', 'frame_count']
        )

    def test_report_should_have_stream_fields_with_proper_values(self):
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['codec_type'] == 'video'
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['codec_name'] == 'mpeg4'
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['start_time'] == '0.000000'

        assert RAW_REPORT_WITH_MPEG4['streams'][1]['codec_type'] == 'audio'
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['codec_name'] == 'mp3'
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['start_time'] == '0.000000'

        report = FfprobeFormatReport(RAW_REPORT_WITH_MPEG4)

        self.assertEqual(report.stream_reports[0].codec_type, 'video')
        self.assertEqual(report.stream_reports[0].codec_name, 'mpeg4')
        self.assertEqual(report.stream_reports[0].start_time.duration, 0)

        self.assertEqual(report.stream_reports[1].codec_type, 'audio')
        self.assertEqual(report.stream_reports[1].codec_name, 'mp3')
        self.assertEqual(report.stream_reports[1].start_time.duration, 0)

    def test_all_stream_properties_are_tested(self):
        self.assertCountEqual(
            FfprobeStreamReport.ATTRIBUTES_TO_COMPARE,
            ['codec_type', 'codec_name', 'start_time']
        )

    def test_report_should_have_format_fields_with_proper_values(self):
        assert RAW_REPORT_WITH_MPEG4['streams'][0]['codec_type'] == 'video'
        assert RAW_REPORT_WITH_MPEG4['streams'][1]['codec_type'] == 'audio'
        assert len(RAW_REPORT_WITH_MPEG4['streams']) == 2
        assert RAW_REPORT_WITH_MPEG4['format']['format_name'] == 'avi'
        assert RAW_REPORT_WITH_MPEG4['format']['duration'] == '5.640000'
        assert RAW_REPORT_WITH_MPEG4['format']['start_time'] == '0.000000'
        assert RAW_REPORT_WITH_MPEG4['format']['nb_programs'] == 0

        report = FfprobeFormatReport(RAW_REPORT_WITH_MPEG4)

        self.assertEqual(report.stream_types, {'audio': 1, 'video': 1})
        self.assertEqual(report.format_name, 'avi')
        self.assertEqual(report.duration.duration, 5.64)
        self.assertEqual(report.start_time.duration, 0)
        self.assertEqual(report.program_count, 0)

    def test_all_format_properties_are_tested(self):
        self.assertCountEqual(
            FfprobeFormatReport.ATTRIBUTES_TO_COMPARE,
            [
                'format_name', 'stream_types', 'duration', 'start_time',
                'program_count'
            ]
        )

    def test_diff_equal_to_expected(self):
        report_original = FfprobeFormatReport(RAW_REPORT_ORIGINAL)
        raw_report_modified = copy.deepcopy(RAW_REPORT_ORIGINAL)
        raw_report_modified['format']['start_time'] = 10
        report_modified = FfprobeFormatReport(raw_report_modified)

        diff = (report_modified.diff(report_original))
        expected_diff = [{'location': 'format', 'attribute': 'start_time',
                          'original_value': FuzzyDuration(10, 0),
                          'modified_value': FuzzyDuration(0.0, 0),
                          'reason': 'Different attribute values'}]

        self.assertCountEqual(diff, expected_diff)

    @parameterized.expand([
        (
            [('format', 'start_time')],
            10,
            [{
                'location': 'format',
                'attribute': 'start_time',
                'original_value': FuzzyDuration(10.0, 0),
                'modified_value': FuzzyDuration(0.0, 0),
                'reason': 'Different attribute values',
            }],
        ),
        (
            [('format', 'duration')],
            80,
            [{
                'location': 'format',
                'attribute': 'duration',
                'original_value': FuzzyDuration(80, 10),
                'modified_value': FuzzyDuration(46.665, 10),
                'reason': 'Different attribute values',
            }],
        ),
        (
            [('format', 'nb_programs')],
            2,
            [{
                'location': 'format',
                'attribute': 'program_count',
                'original_value': 2,
                'modified_value': 0,
                'reason': 'Different attribute values',
            }],
        ),
        (
            [('streams', 0, 'codec_name')],
            'flv',
            [{
                'location': 'video',
                'attribute': 'codec_name',
                'original_value': 'flv',
                'modified_value': 'h264',
                'reason': 'Different attribute values',
                'original_stream_index': 0,
                'modified_stream_index': 0,
            }],
        ),
        (
            [('streams', 1, 'start_time')],
            '0.5',
            [{
                'location': 'audio',
                'attribute': 'start_time',
                'original_value': FuzzyDuration(0.5, 0.05),
                'modified_value': FuzzyDuration(0.012, 0.05),
                'reason': 'Different attribute values',
                'original_stream_index': 1,
                'modified_stream_index': 1,
            }],
        ),
        (
            [('streams', 1, 'duration')],
            '0.5',
            [{
                'location': 'audio',
                'attribute': 'duration',
                'original_value': FuzzyDuration(0.5, 0.05),
                'modified_value': None,
                'reason': 'Different attribute values',
                'original_stream_index': 1,
                'modified_stream_index': 1,
            }],
        ),
        (
            [('streams', 0, 'width')],
            1920,
            [{
                'location': 'video',
                'attribute': 'resolution',
                'original_value': (1920, 576),
                'modified_value': (1024, 576),
                'reason': 'Different attribute values',
                'original_stream_index': 0,
                'modified_stream_index': 0,
            }],
        ),
        (
            [('streams', 0, 'resolution')],
            (1920, 1080),
            [{
                'location': 'video',
                'attribute': 'resolution',
                'original_value': ((1920, 1080), 1024, 576),
                'modified_value': (1024, 576),
                'reason': 'Different attribute values',
                'original_stream_index': 0,
                'modified_stream_index': 0,
            }],
        ),
        (
            [('streams', 0, 'resolution')],
            (1024, 576),
            [],
        ),

        (
            [('streams', 0, 'r_frame_rate')],
            '12/1',
            [{
                'location': 'video',
                'attribute': 'frame_rate',
                'original_value': 12,
                'modified_value': 24,
                'reason': 'Different attribute values',
                'original_stream_index': 0,
                'modified_stream_index': 0,
            }],
        ),
        (
            [('streams', 1, 'sample_rate')],
            '24000',
            [{
                'location': 'audio',
                'attribute': 'sample_rate',
                'original_value': 24000,
                'modified_value': 48000,
                'reason': 'Different attribute values',
                'original_stream_index': 1,
                'modified_stream_index': 1,
            }],
        ),
        (
            [('streams', 4, 'tags', 'language')],
            'eng',
            [{
                'location': 'subtitle',
                'attribute': 'language',
                'original_value': 'eng',
                'modified_value': 'ger',
                'reason': 'Different attribute values',
                'original_stream_index': 4,
                'modified_stream_index': 4,
            }],
        ),
        (
            [('streams', 1, 'bit_rate')],
            '499524',
            [{
                'location': 'audio',
                'attribute': 'bitrate',
                'original_value': FuzzyInt(499524, 5),
                'modified_value': None,
                'reason': 'Different attribute values',
                'original_stream_index': 1,
                'modified_stream_index': 1,
            }],
        ),
    ])
    def test_that_changed_raw_report_field_is_reported_in_diff(
            self,
            dict_path,
            new_value,
            expected_diff,
    ):
        report_original = FfprobeFormatReport(RAW_REPORT_ORIGINAL)
        raw_report_modified = copy.deepcopy(RAW_REPORT_ORIGINAL)
        raw_report_modified = self._change_value_in_dict(
            dict_path,
            new_value,
            raw_report_modified,
        )
        assert raw_report_modified != RAW_REPORT_ORIGINAL
        report_modified = FfprobeFormatReport(raw_report_modified)

        diff = report_modified.diff(report_original)
        self.assertEqual(diff, expected_diff)

    @parameterized.expand([
        (
            [('format', 'start_time')],
            10,
            {'format': {'start_time': 0}},
        ),
        (
            [('format', 'duration')],
            80,
            {'format': {'duration': 46.665}},
        ),
        (
            [('format', 'nb_programs')],
            2,
            {'format': {'program_count': 0}},
        ),
        (
            [('streams', 0, 'codec_name')],
            'h265',
            {'video': {'codec_name': 'h264'}},
        ),
        (
            [
                ('streams', 1, 'codec_name'),
                ('streams', 8, 'codec_name'),
            ],
            'xx',
            {'audio': {'codec_name': 'aac'}},
        ),
    ])
    def test_that_override_in_diff_should_work_correctly(
            self,
            dict_path,
            new_value,
            overrides,
    ):
        report_original = FfprobeFormatReport(RAW_REPORT_ORIGINAL)
        raw_report_modified = copy.deepcopy(RAW_REPORT_ORIGINAL)
        raw_report_modified = self._change_value_in_dict(
            dict_path,
            new_value,
            raw_report_modified
        )
        assert raw_report_modified != RAW_REPORT_ORIGINAL

        report_modified = FfprobeFormatReport(raw_report_modified)
        diff = (report_original.diff(
            modified_report=report_modified,
            overrides=overrides,
        ))
        self.assertEqual(diff, [])

    @parameterized.expand([
        (
            [('format', 'start_time')],
            100,
            {'format': {'start_time'}},
        ),
        (
            [('format', 'duration')],
            80,
            {'format': {'duration'}},
        ),
        (
            [('format', 'nb_programs')],
            2,
            {'format': {'program_count'}},
        ),
        (
            [('streams', 0, 'codec_name')],
            'flv',
            {'video': {'codec_name'}},
        ),
        (
            [
                ('streams', 1, 'codec_name'),
                ('streams', 8, 'codec_name'),
            ],
            'xx',
            {'audio': {'codec_name': 'aac'}},
        ),
    ])
    def test_that_exclude_in_diff_should_work_correctly(
            self,
            fields_to_change,
            new_value,
            excludes,
    ):

        report_original = FfprobeFormatReport(RAW_REPORT_ORIGINAL)
        raw_report_modified = copy.deepcopy(RAW_REPORT_ORIGINAL)
        raw_report_modified = self._change_value_in_dict(
            fields_to_change,
            new_value,
            raw_report_modified,
        )
        assert raw_report_modified != RAW_REPORT_ORIGINAL

        report_modified = FfprobeFormatReport(raw_report_modified)
        diff = (report_original.diff(
            modified_report=report_modified,
            excludes=excludes,
        ))
        self.assertEqual(diff, [])


class TestFuzzyDuration(TestCase):
    @parameterized.expand([
        (100.0, 0, 100, 0),
        (80, 10.0, 100, 10),
        (10, 20, -20, 20),
        (110, 0, 100, 10),
    ])
    def test_that_fuzzy_durations_should_be_equal_if_such_parameters_given(
            self,
            duration_1,
            tolerance_1,
            duration_2,
            tolerance_2,
    ):
        self.assertEqual(
            FuzzyDuration(duration_1, tolerance_1),
            FuzzyDuration(duration_2, tolerance_2)
        )

    @parameterized.expand([
        (100.0, 0, 99.9, 0),
        (80, 9.9, 100, 10),
        (10, 10, -20, 10),
        (100, 0, 120, 10),
    ])
    def test_that_fuzzy_durations_should_not_be_equal_if_such_parameters_given(
            self,
            duration_1,
            tolerance_1,
            duration_2,
            tolerance_2,
    ):
        self.assertNotEqual(
            FuzzyDuration(duration_1, tolerance_1),
            FuzzyDuration(duration_2, tolerance_2)
        )


class TestFuzzyInt(TestCase):
    @parameterized.expand([
        (100, 0, 100, 0),
        (80, 10, 88, 0),
        (60, 0, 100, 40),
        (120, 10, 100, 10),
    ])
    def test_that_fuzzy_int_should_be_equal_if_such_parameters_given(
            self,
            value_1,
            tolerance_percent_1,
            value_2,
            tolerance_percent_2,
    ):
        self.assertEqual(
            FuzzyInt(value_1, tolerance_percent_1),
            FuzzyInt(value_2, tolerance_percent_2)
        )

    @parameterized.expand([
        (101, 0, 100, 0),
        (80, 10, 100, 10),
        (60, 40, 100, 0),
        (100, 2, 120, 10),
    ])
    def test_that_fuzzy_int_should_not_be_equal_if_such_parameters_given(
            self,
            value_1,
            tolerance_percent_1,
            value_2,
            tolerance_percent_2,
    ):
        self.assertNotEqual(
            FuzzyInt(value_1, tolerance_percent_1),
            FuzzyInt(value_2, tolerance_percent_2)
        )


class TestBuild(TempDirFixture, PrepareDockerTaskMixin):
    def setUp(self):
        super(TestBuild, self).setUp()
        self.prepare_docker_task_thread_for_tests(self.new_path)

    @pytest.mark.slow
    def test_build_should_return_list_with_one_ffprobe_format_report_instance(
            self):
        reports = FfprobeFormatReport.build(
            tmp_dir='/tmp/',
            video_paths=[self.RESOURCE_STREAM]
        )
        self.assertIsInstance(reports, List)
        self.assertEqual(len(reports), 1)
        self.assertIsInstance(reports[0], FfprobeFormatReport)
