import os

import mock
import pytest
from parameterized import parameterized

from apps.transcoding.common import VideoCodec, Container
from golem.testutils import TestTaskIntegration
from tests.apps.ffmpeg.task.ffprobe_report import FfprobeFormatReport, FuzzyInt
from tests.apps.ffmpeg.task.ffprobe_report_set import FfprobeReportSet
from tests.apps.ffmpeg.task.simulated_transcoding_operation import \
    SimulatedTranscodingOperation


class TestSimulatedTranscodingOperationIntegration(TestTaskIntegration):

    def setUp(self):
        super(TestSimulatedTranscodingOperationIntegration, self).setUp()

        self.RESOURCES = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'resources')

        self.operation = SimulatedTranscodingOperation(
            task_executor=self,
            experiment_name="codec change",
            resource_dir=self.RESOURCES,
            tmp_dir=self.tempdir)
        self.ffprobe_report_set = FfprobeReportSet()
        self.operation.attach_to_report_set(self.ffprobe_report_set)

    @pytest.mark.slow
    def test_run_returns_correct_variables_instances(self):
        self.operation.request_video_codec_change(VideoCodec.H_264)
        self.operation.request_container_change(Container.MP4)
        input_report, output_report, diff = self.operation.run('test_video.mp4')

        self.assertIsInstance(input_report, FfprobeFormatReport)
        self.assertIsInstance(output_report, FfprobeFormatReport)
        self.assertIsInstance(diff, list)
        self.assertIn(
            'h264/mp4/2seg',
            self.ffprobe_report_set._report_tables['codec change']['test_video.mp4']  # noqa pylint: disable=line-too-long
        )

    @mock.patch('golem.testutils.TestTaskIntegration.execute_task',
                side_effect=BaseException)
    def test_exception_during_task_execution_is_collected(self, _executor):
        self.operation.request_video_codec_change(VideoCodec.H_264)
        self.operation.request_container_change(Container.MP4)
        with self.assertRaises(BaseException):
            _input, _output, _diff = self.operation.run('test_video.mp4')
        self.assertEqual(
            self.ffprobe_report_set._report_tables,
            {'codec change': {
                'test_video.mp4': {'h264/mp4/2seg': 'BaseException'}}}
        )

    @parameterized.expand([
        ('request_container_change',
         Container.MPEG,
         {'format': {'format_name': 'mpeg'}}),

        ('request_video_codec_change',
         VideoCodec.AV1,
         {'video': {'codec_name': 'av1'}}),

        ('request_video_bitrate_change',
         100,
         {'video': {'bitrate': FuzzyInt(100, 5)}}),

        ('request_resolution_change',
         'custom_value',
         {'video': {'resolution': 'custom_value'}}),

        ('request_frame_rate_change',
         'custom_value',
         {'video': {'frame_rate': 'custom_value'}}),


    ])
    def test_diff_overrides_are_equal_to_expeted_if_function_changing_parameter_called(  # noqa pylint: disable=line-too-long
            self,
            function_name,
            new_value,
            expected_diff_overrides,
    ):
        function = getattr(self.operation, function_name)
        function(new_value)
        diff_overrides = self.operation._diff_overrides
        self.assertEqual(expected_diff_overrides, diff_overrides)

    @parameterized.expand([
        (['format'], [{'format_name'}]),
        (['video'], [{'codec_name', 'bitrate'}]),
        (['video'], [{'codec_name', 'bitrate'}]),
        (['video'], [{'resolution', 'bitrate'}]),
        (['format', 'video'], [{'format_name'}, {'bitrate'}]),
        (['format', 'video'], [{'format_name'}, {'resolution', 'bitrate'}]),
    ])
    def test_exclude_from_diff_excludes_parameters_correctly(
            self,
            location,
            fieldname,
    ):
        exclude = dict(zip(location, fieldname))
        self.operation.exclude_from_diff(exclude)
        self.assertEqual(self.operation._diff_excludes, exclude)
