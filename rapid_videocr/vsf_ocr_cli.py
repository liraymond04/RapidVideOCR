# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
import argparse
from enum import Enum
from pathlib import Path

from .main import OutputFormat, RapidVideOCR, RapidVideOCRInput
from .utils.logger import Logger
from .utils.utils import float_range
from .vsf_cli import VideoSubFinder, VideoSubFinderInput


class VideoFormat(Enum):
    MP4 = ".mp4"
    AVI = ".avi"
    MOV = ".mov"
    MKV = ".mkv"


class RapidVideoSubFinderOCR:
    def __init__(
        self,
        vsf_input_params: VideoSubFinderInput,
        ocr_input_params: RapidVideOCRInput,
    ):
        self.logger = Logger(logger_name=__name__).get_log()
        self.vsf = VideoSubFinder(vsf_input_params)
        self.video_ocr = RapidVideOCR(ocr_input_params)
        self.video_formats = [VideoFormat[v].value for v in VideoFormat.__members__]

    def __call__(self, video_path: str, output_dir: str = "outputs"):
        if Path(video_path).is_dir():
            video_list = Path(video_path).rglob("*.*")
            video_list = [
                v for v in video_list if v.suffix.lower() in self.video_formats
            ]
        else:
            video_list = [video_path]

        self.logger.info(
            "Extracting subtitle images with VideoSubFinder (takes quite a long time) ..."
        )
        video_num = len(video_list)
        for i, one_video in enumerate(video_list):
            self.logger.info(
                "[%s/%s] Starting to extract %s key frame", i + 1, video_num, one_video
            )

            save_name = Path(one_video).stem
            save_dir = Path(output_dir) / save_name
            save_vsf_dir = save_dir / "VSF_Results"

            try:
                self.vsf(str(one_video), str(save_vsf_dir))
            except Exception as e:
                self.logger.error("Extract %s error, %s, skip", one_video, e)
                continue

            self.logger.info(
                "[%s/%s] Starting to run %s ocr", i + 1, video_num, one_video
            )

            rgb_dir = Path(save_vsf_dir) / "RGBImages"
            if not list(rgb_dir.iterdir()):
                self.logger.warning("Extracting frames from %s is 0, skip", one_video)
                continue
            self.video_ocr(rgb_dir, save_dir, save_name=save_name)


def main():
    parser = argparse.ArgumentParser()

    videocr_param_group = parser.add_argument_group(title="VideOCRParameters")
    videocr_param_group.add_argument(
        "-video_dir",
        "--video_dir",
        type=str,
        default=None,
        help="The full path of video or the path of video directory.",
    )
    videocr_param_group.add_argument(
        "-i",
        "--img_dir",
        type=str,
        default=None,
        help="The full path of RGBImages or TXTImages.",
    )
    videocr_param_group.add_argument(
        "-s",
        "--save_dir",
        type=str,
        default="outputs",
        help='The path of saving the recognition result. Default is "outputs" under the current directory.',
    )
    videocr_param_group.add_argument(
        "-o",
        "--out_format",
        type=str,
        default=OutputFormat.ALL.value,
        choices=[OutputFormat[v].value for v in OutputFormat.__members__],
        help='Output file format. Default is "all".',
    )
    videocr_param_group.add_argument(
        "--is_batch_rec",
        action="store_true",
        default=False,
        help="Which mode to run (concat recognition or single recognition). Default is False.",
    )
    videocr_param_group.add_argument(
        "-b",
        "--batch_size",
        type=int,
        default=10,
        help="The batch of concating image nums in concat recognition mode. Default is 10.",
    )

    vsf_param_group = parser.add_argument_group(title="VSFParameters")
    vsf_param_group.add_argument(
        "-vsf",
        "--vsf_exe_path",
        type=str,
        default=None,
        help="The full path of VideoSubFinderWXW.exe.",
    )
    vsf_param_group.add_argument(
        "-c",
        "--clear_dirs",
        action="store_false",
        default=True,
        help="Clear Folders (remove all images), performed before any other steps. Default is True",
    )
    vsf_param_group.add_argument(
        "-r",
        "--run_search",
        action="store_false",
        default=True,
        help="Run Search (find frames with hardcoded text (hardsub) on video) Default is True",
    )
    vsf_param_group.add_argument(
        "-ccti",
        "--create_cleared_text_images",
        action="store_true",
        default=False,
        help="Create Cleared Text Images. Default is True",
    )
    vsf_param_group.add_argument(
        "-ces",
        "--create_empty_sub",
        type=str,
        default=None,
        help="Create Empty Sub With Provided Output File Name (*.ass or *.srt)",
    )
    vsf_param_group.add_argument(
        "-cscti",
        "--create_sub_from_cleared_txt_images",
        type=str,
        default=None,
        help="Create Sub From Cleared TXT Images With Provided Output File Name (*.ass or *.srt)",
    )
    vsf_param_group.add_argument(
        "-cstxt",
        "--create_sub_from_txt_results",
        type=str,
        default=None,
        help="Create Sub From TXT Results With Provided Output File Name (*.ass or *.srt)",
    )
    vsf_param_group.add_argument(
        "-ovocv",
        "--open_video_opencv",
        action="store_false",
        default=True,
        help="open video by OpenCV (default). Default is True",
    )
    vsf_param_group.add_argument(
        "-ovffmpeg",
        "--open_video_ffmpeg",
        action="store_true",
        default=False,
        help="open video by FFMPEG",
    )
    vsf_param_group.add_argument(
        "-uc", "--use_cuda", action="store_true", default=False, help="use cuda"
    )
    vsf_param_group.add_argument(
        "--start_time",
        type=str,
        default="0:00:00:000",
        help="start time, default = 0:00:00:000 (in format hour:min:sec:milisec)",
    )
    vsf_param_group.add_argument(
        "--end_time",
        type=str,
        default=None,
        help="end time, default = video length",
    )
    vsf_param_group.add_argument(
        "-te",
        "--top_video_image_percent_end",
        type=float_range(0, 1.0),
        default=0.2,
        help="top video image percent offset from image bottom, can be in range [0.0,1.0], default = 1.0",
    )
    vsf_param_group.add_argument(
        "-be",
        "--bottom_video_image_percent_end",
        type=float_range(0, 1.0),
        default=0.0,
        help="bottom video image percent offset from image bottom, can be in range [0.0,1.0], default = 0.0",
    )
    vsf_param_group.add_argument(
        "-le",
        "--left_video_image_percent_end",
        type=float_range(0, 1.0),
        default=0.0,
        help="left video image percent end, can be in range [0.0,1.0], default = 0.0",
    )
    vsf_param_group.add_argument(
        "-re",
        "--right_video_image_percent_end",
        type=float_range(0, 1.0),
        default=1.0,
        help="right video image percent end, can be in range [0.0,1.0], default = 1.0",
    )
    vsf_param_group.add_argument(
        "-gs",
        "--general_settings",
        default=None,
        help="general settings (path to general settings *.cfg file, default = settings/general.cfg)",
    )
    vsf_param_group.add_argument(
        "-nthr",
        "--num_threads",
        type=int,
        default=1,
        help="number of threads used for Run Search",
    )
    vsf_param_group.add_argument(
        "-nocrthr",
        "--num_ocr_threads",
        type=int,
        default=1,
        help="number of threads used for Create Cleared TXT Images",
    )
    args = parser.parse_args()

    ocr_input_params = RapidVideOCRInput(
        is_batch_rec=args.is_batch_rec,
        batch_size=args.batch_size,
        out_format=args.out_format,
    )

    if args.vsf_exe_path and args.video_dir:
        vsf_input_params = VideoSubFinderInput(**vars(args))
        extractor = RapidVideoSubFinderOCR(vsf_input_params, ocr_input_params)
        extractor(args.video_dir, args.save_dir)
    elif args.img_dir:
        extractor = RapidVideOCR(ocr_input_params)
        extractor(args.img_dir, args.save_dir)
    else:
        pass


if __name__ == "__main__":
    main()
