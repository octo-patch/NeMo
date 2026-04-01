# Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Generate comparison reports for MagpieTTS evaluation buckets.

This script compares two evaluation buckets produced by `magpietts_inference`
and generates:
1. a Markdown evaluation report with aggregated and per-benchmark metrics;
2. an optional audio comparison report, either:
    - as a local self-contained HTML file with embedded base64 audio, or
    - as an S3-hosted HTML report with audio uploaded separately and referenced 
        through presigned links.

The script supports:
- local buckets,
- remote buckets accessed over SSH,
- optional upload of the audio report to S3-compatible object storage.

Terminology
-----------

A "bucket" in this script means the root directory of one evaluation run.
Inside that root, evaluation artifacts are expected to live inside the
subdirectory given by `--results_subdir` (default: `results`).

Typical layouts:

Local generation:
    <experiment_root>/<results_subdir>/...

Cluster / Slurm generation:
    <experiment_root>/<results_subdir>/...

In both cases, `--baseline_path` and `--candidate_path` should point to the
experiment root, while `--results_subdir` points to the subdirectory that
contains metrics and generated audio.

Examples
--------

1. Generate only the Markdown evaluation report from local buckets:

```bash
python examples/tts/magpietts_comparison_report.py \
  --baseline_name "Model A" \
  --baseline_path /workspace/NeMo/exp/buckets/baseline \
  --candidate_name "Model B" \
  --candidate_path /workspace/NeMo/exp/buckets/candidate \
  --task_id NEMOTTS-2007 \
  --output_dir /workspace/NeMo/exp/reports
```

2. Generate reports when evaluation artifacts are stored in a non-default results subdirectory:

```bash
python examples/tts/magpietts_comparison_report.py \
  --baseline_name "Model A" \
  --baseline_path /workspace/NeMo/exp/buckets/baseline \
  --candidate_name "Model B" \
  --candidate_path /workspace/NeMo/exp/buckets/candidate \
  --results_subdir res \
  --task_id NEMOTTS-2007 \
  --output_dir /workspace/NeMo/exp/reports
```

3. Generate the Markdown report from remote buckets over SSH:

```bash
export REMOTE_HOST_KEY='your_ssh_password'
```

```bash
python examples/tts/magpietts_comparison_report.py \
  --baseline_name "Model A" \
  --baseline_path /mnt/exps/baseline \
  --candidate_name "Model B" \
  --candidate_path /mnt/exps/candidate \
  --remote_hostname your_remote_host \
  --remote_username your_user \
  --task_id NEMOTTS-2007 \
  --output_dir /workspace/NeMo/exp/reports
```

4. Generate a local audio comparison report with embedded audio:

```bash
python examples/tts/magpietts_comparison_report.py \
  --baseline_name "Model A" \
  --baseline_path /workspace/NeMo/exp/buckets/baseline \
  --candidate_name "Model B" \
  --candidate_path /workspace/NeMo/exp/buckets/candidate \
  --audio_report \
  --audio_report_benchmarks libritts_test_clean,riva_hard_digits,vctk \
  --samples_per_benchmark 30 \
  --audio_report_comment "Inference params: T=0.6, top-k=80." \
  --task_id NEMOTTS-2007 \
  --output_dir /workspace/NeMo/exp/reports
```

5. Upload the audio comparison report to S3-compatible storage:

```bash
export S3_ACCESS_KEY_ID='your_s3_key_id' S3_SECRET_ACCESS_KEY='your_s3_secret'
```

```bash
python examples/tts/magpietts_comparison_report.py \
  --baseline_name "Model A" \
  --baseline_path /workspace/NeMo/exp/buckets/baseline \
  --candidate_name "Model B" \
  --candidate_path /workspace/NeMo/exp/buckets/candidate \
  --audio_report \
  --upload_audio_report_to_s3 \
  --s3_endpoint https://your-s3-endpoint \
  --s3_bucket your_bucket_name \
  --s3_region us-west-2 \
  --audio_report_benchmarks libritts_test_clean,riva_hard_digits,vctk \
  --samples_per_benchmark 30 \
  --audio_report_comment "Inference params: T=0.6, top-k=80." \
  --task_id NEMOTTS-2007 \
  --output_dir /workspace/NeMo/exp/reports
```

6. Use both remote SSH input buckets and S3 upload for the audio report:

```bash
export REMOTE_HOST_KEY='your_ssh_password' S3_ACCESS_KEY_ID='your_s3_key_id' S3_SECRET_ACCESS_KEY='your_s3_secret'
```

```bash
python examples/tts/magpietts_comparison_report.py \
  --baseline_name "Model A" \
  --baseline_path /mnt/exps/baseline \
  --candidate_name "Model B" \
  --candidate_path /mnt/exps/candidate \
  --remote_hostname your_remote_host \
  --remote_username your_user \
  --audio_report \
  --upload_audio_report_to_s3 \
  --s3_endpoint https://your-s3-endpoint \
  --s3_bucket your_bucket_name \
  --s3_region us-west-2 \
  --audio_report_benchmarks libritts_test_clean,riva_hard_digits,vctk \
  --samples_per_benchmark 30 \
  --audio_report_comment "Inference params: T=0.6, top-k=80." \
  --task_id NEMOTTS-2007 \
  --output_dir /workspace/NeMo/exp/reports
```

Environment variables
--------

SSH access:
- `REMOTE_HOST_KEY` - password used for SSH authentication.

S3 upload:
- `S3_ACCESS_KEY_ID` - S3 access key,
- `S3_SECRET_ACCESS_KEY` - S3 secret key.

Notes
--------
- `magpietts_inference` supports several repetitions, but this script compares
    only artifacts from repetition `0`.
- `--results_subdir` is not the experiment root. It is the subdirectory inside
    the experiment root that contains evaluation outputs such as metrics and
    generated audio. If buckets were generated locally, `--results_subdir` may
    need to be set to an empty string.
- The local audio report embeds audio directly into HTML using base64. This
    makes the report fully self-contained, but it can become large.
- The S3 audio report uploads audio files separately and generates an HTML page
    that references them through presigned URLs.
- Presigned S3 links expire. The generated S3-backed audio report includes the
    expiration time directly in the HTML page. The default expiration time is one year.
- The expiration time is also included as a suffix in the uploaded artifacts
    directory name, using the format `%Y-%m-%dT%H-%M-%SZ`, so uploaded reports
    can be filtered and deleted later if needed.
"""
import argparse
import base64
import hashlib
import html
import json
import logging
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from stat import S_ISDIR
from typing import Any, BinaryIO, Generator, Optional, Self

import boto3
import numpy as np
from botocore.config import Config
from paramiko import AutoAddPolicy, SSHClient
from paramiko.sftp_client import SFTPClient
from scipy.stats import mannwhitneyu
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger(__name__)


_REMOTE_HOST_KEY: str = "REMOTE_HOST_KEY"
_S3_ACCESS_KEY_ID: str = "S3_ACCESS_KEY_ID"
_S3_SECRET_ACCESS_KEY: str = "S3_SECRET_ACCESS_KEY"
_S3_LINK_EXPIRES_IN: int = 31536000  # One year in seconds.

_DUMMY_TASK_ID: str = "NEMOTTS-0000"
_TQDM_NCOLS: int = 80
_SIGNIFICANCE_LEVEL: float = 0.05
_P_VAL_ROUND_DIGITS: int = 4
_SEED: int = 42

random.seed(_SEED)

_BENCHMARK_NAMES: tuple[str, ...] = tuple(
    sorted(
        [
            "libritts_seen",
            "libritts_test_clean",
            "riva_hard_digits",
            "riva_hard_letters",
            "riva_hard_money",
            "riva_hard_short",
            "vctk",
        ],
        key=len,
        reverse=True,
    )
)
_AUDIO_REPORT_HEADER_BLOCK: str = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Audio Comparison Report</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 40px;
    }
    h1, h2, h3 {
      text-align: left;
    }
    p.comment {
      text-align: left;
      font-style: italic;
      color: #555;
      margin-bottom: 25px;
    }
    p.expiration_comment {
      text-align: left;
      font-style: italic;
      color: #CD5C5C;
      margin-bottom: 25px;
    }
    .pair-row {
      display: flex;
      gap: 20px;
      align-items: center;
      justify-content: flex-start;
      margin-bottom: 25px;
    }
    .audio-box {
      flex: 0 0 auto;
      text-align: left;
      margin-top: 5px;
      margin-bottom: 0px;
    }
    .pair-comment {
      font-style: italic;
      color: #666;
      margin-left: 5px;
      margin-top: 0px;
      margin-bottom: 35px;
    }
  </style>
</head><body>
"""


@dataclass(frozen=True)
class _MetricSpec:
    # Metric key expected in the aggregated metrics JSON.
    name: str
    # Metric name shown in the report tables.
    report_name: str
    # Whether smaller values are better; None means no winner highlighting.
    lower_is_better: Optional[bool]
    # Number of decimal digits used when formatting the metric value.
    round_digits: int
    # Optional unit suffix appended to the formatted metric value.
    units: str = ""
    # Scale factor applied before formatting, e.g. 100 for percentages.
    multiplier: float | int = 1
    # Whether this metric should appear in the cross-benchmark summary table.
    include_in_summary: bool = True
    # Whether this metric may be absent from bucket metrics without causing an error.
    optional: bool = False


@dataclass(frozen=True)
class _StatTestMetricSpec:
    # Metric key expected in the filewise metrics JSON used for statistical testing.
    name: str
    # Metric name shown in the statistical test tables.
    report_name: str
    # Whether smaller values indicate better quality for winner selection.
    lower_is_better: Optional[bool]


_METRICS: list[_MetricSpec] = [
    _MetricSpec("wer_cumulative", "WER (cumulative)", True, 2, "%", 100),
    _MetricSpec("cer_cumulative", "CER (cumulative)", True, 2, "%", 100),
    _MetricSpec("wer_filewise_avg", "WER (filewise avg)", True, 2, "%", 100),
    _MetricSpec("cer_filewise_avg", "CER (filewise avg)", True, 2, "%", 100),
    _MetricSpec("utmosv2_avg", "UTMOS v2", False, 3),
    _MetricSpec("ssim_pred_gt_avg", "SSIM (pred vs GT)", False, 4),
    _MetricSpec("ssim_pred_context_avg", "SSIM (pred vs context)", False, 4),
    _MetricSpec("eou_cutoff_rate", "EoU cut-off rate", True, 3, "", 1, False, True),
    _MetricSpec("eou_silence_rate", "EoU silence rate", True, 3, "", 1, False, True),
    _MetricSpec("eou_noise_rate", "EoU noise rate", True, 3, "", 1, False, True),
    _MetricSpec("eou_error_rate", "EoU error rate", True, 3, "", 1, False, True),
    _MetricSpec("total_gen_audio_seconds", "Total audio (sec)", None, 1, "", 1, False),
]


_STAT_TEST_METRICS: list[_StatTestMetricSpec] = [
    _StatTestMetricSpec("wer", "WER", True),
    _StatTestMetricSpec("cer", "CER", True),
    _StatTestMetricSpec("utmosv2", "UTMOS v2", False),
    _StatTestMetricSpec("pred_context_ssim", "SSIM (pred vs context)", False),
]


class _Winner(str, Enum):
    baseline = "baseline"
    candidate = "candidate"
    tie = "tie"


class _Alternative(str, Enum):
    two_sided = "two-sided"
    greater = "greater"
    less = "less"


@dataclass
class _BucketStructure:
    eval_output_subdir: str = "results"
    metrics_suffix: str = "_metrics_0.json"
    metrics_filewise_suffix: str = "_filewise_metrics_0.json"
    generated_audio_dir: str = "audio/repeat_0"
    generated_audio_prefix: str = "predicted_audio_"


class _Storage(ABC):

    @abstractmethod
    def exists(self, path: Path) -> bool: ...

    @abstractmethod
    def iter_dir(
        self,
        path: Path,
        only_dirs: bool = False,
    ) -> Generator[Path, None, None]: ...

    @abstractmethod
    def open_file(self, path: Path) -> BinaryIO: ...

    @abstractmethod
    def read_json(self, path: Path) -> Any: ...

    @abstractmethod
    def read_bytes(self, path: Path) -> bytes: ...


class _LocalStorage(_Storage):

    def exists(self, path: Path) -> bool:
        return path.exists()

    def iter_dir(
        self,
        path: Path,
        only_dirs: bool = False,
    ) -> Generator[Path, None, None]:
        for p in path.iterdir():
            if only_dirs and not p.is_dir():
                continue
            yield p

    def open_file(self, path: Path) -> BinaryIO:
        return open(path, "rb")

    def read_json(self, path: Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()


class _SFTPStorage(_Storage):

    def __init__(self, sftp: SFTPClient) -> None:
        super().__init__()
        self.sftp = sftp

    def exists(self, path: Path) -> bool:
        try:
            self.sftp.stat(path.as_posix())
            return True

        except FileNotFoundError:
            return False

        except OSError:
            return False

    def iter_dir(
        self,
        path: Path,
        only_dirs: bool = False,
    ) -> Generator[Path, None, None]:
        for item in self.sftp.listdir_attr(path.as_posix()):
            if only_dirs and not S_ISDIR(item.st_mode):
                continue
            yield path / item.filename

    def open_file(self, path: Path) -> BinaryIO:
        return self.sftp.open(path.as_posix(), "rb")

    def read_json(self, path: Path) -> Any:
        with self.sftp.open(path.as_posix(), "rb") as f:
            data = json.loads(f.read().decode("utf-8"))
        return data

    def read_bytes(self, path: Path) -> bytes:
        with self.sftp.open(path.as_posix(), "rb") as f:
            data = f.read()
        return data


@dataclass(frozen=True)
class _BenchmarkSampleMeta:
    name: str
    text: str
    sample_id: str

    @staticmethod
    def _validate(item: dict[str, Any]) -> None:
        for key in ["pred_audio_filepath", "gt_text", "gt_audio_filepath", "context_audio_filepath"]:
            if key not in item:
                raise ValueError(f"Missing required key '{key}' in filewise metrics item.")

    @staticmethod
    def _get_sample_id(item: dict[str, Any]) -> str:
        parts = [item["gt_audio_filepath"], item["context_audio_filepath"]]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    @classmethod
    def from_filewise_metrics_item(cls, item: dict[str, Any]) -> Self:
        cls._validate(item)

        obj = cls(
            name=Path(item["pred_audio_filepath"]).stem,
            text=item["gt_text"],
            sample_id=cls._get_sample_id(item),
        )
        return obj


@dataclass
class _BenchmarkData:
    name: str
    metrics_path: Optional[Path] = None
    filewise_metrics_path: Optional[Path] = None
    generated_audio_paths: dict[str, Path] = field(default_factory=dict)

    metrics: Optional[dict[str, float]] = None
    filewise_metrics: Optional[list[dict[str, Any]]] = None

    @classmethod
    def from_storage(
        cls,
        benchmark_name: str,
        benchmark_path: Path,
        bucket_structure: _BucketStructure,
        check_audio: bool,
        storage: _Storage,
    ) -> Self:
        obj = cls(name=benchmark_name)

        path = benchmark_path / f"{benchmark_name}{bucket_structure.metrics_suffix}"
        if not storage.exists(path):
            raise FileNotFoundError(f"Missing metrics file: '{path}'.")
        obj.metrics_path = path

        path = benchmark_path / f"{benchmark_name}{bucket_structure.metrics_filewise_suffix}"
        if not storage.exists(path):
            raise FileNotFoundError(f"Missing filewise metrics file: '{path}'.")
        obj.filewise_metrics_path = path

        if check_audio:
            path = benchmark_path / bucket_structure.generated_audio_dir
            if not storage.exists(path):
                raise FileNotFoundError(f"Missing generated audio directory: '{path}'.")

            for p in storage.iter_dir(path):
                if not p.stem.startswith(bucket_structure.generated_audio_prefix) or p.suffix != ".wav":
                    continue
                obj.generated_audio_paths[p.stem] = p

        return obj

    def load_metrics(self, storage: _Storage) -> None:
        if self.metrics_path is None:
            return

        data = storage.read_json(self.metrics_path)

        if not isinstance(data, dict):
            raise TypeError(f"Metrics file must contain a JSON object: '{self.metrics_path}'.")

        self.metrics = data

    def load_filewise_metrics(self, storage: _Storage) -> None:
        if self.filewise_metrics_path is None:
            return

        data = storage.read_json(self.filewise_metrics_path)

        if not isinstance(data, list):
            raise TypeError(f"Filewise metrics file must contain a JSON array: '{self.filewise_metrics_path}'.")

        self.filewise_metrics = data


@dataclass
class _BucketData:
    name: str
    path: Path
    benchmarks: dict[str, _BenchmarkData] = field(default_factory=dict)

    @classmethod
    def from_storage(
        cls,
        bucket_name: str,
        bucket_path: Path,
        bucket_structure: _BucketStructure,
        check_audio: bool,
        storage: _Storage,
    ) -> Self:
        obj = cls(name=bucket_name, path=bucket_path)
        results_path = bucket_path / bucket_structure.eval_output_subdir

        if not storage.exists(results_path):
            raise FileNotFoundError(f"Missing results directory: '{results_path}'.")

        for benchmark_path in storage.iter_dir(results_path, only_dirs=True):
            dir_name = benchmark_path.name
            name = next((n for n in _BENCHMARK_NAMES if dir_name == n or dir_name.endswith(f"_{n}")), None)

            if name is None:
                continue

            obj.benchmarks[name] = _BenchmarkData.from_storage(
                benchmark_name=name,
                benchmark_path=benchmark_path,
                bucket_structure=bucket_structure,
                check_audio=check_audio,
                storage=storage,
            )

        return obj

    def load_metrics(self, storage: _Storage) -> None:
        for benchmark_data in tqdm(self.benchmarks.values(), ncols=_TQDM_NCOLS):
            benchmark_data.load_metrics(storage)
            benchmark_data.load_filewise_metrics(storage)

    def get_metric_avg_value(
        self,
        benchmark_name: str,
        metric_name: str,
    ) -> Optional[float]:
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Unknown benchmark: '{benchmark_name}'.")

        if self.benchmarks[benchmark_name].metrics is None:
            raise ValueError(f"Metrics not loaded for benchmark: '{benchmark_name}'.")

        if metric_name not in self.benchmarks[benchmark_name].metrics:
            return None

        return self.benchmarks[benchmark_name].metrics[metric_name]

    def get_metric_stats(
        self,
        benchmark_name: str,
        metric_name: str,
    ) -> list[float]:
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Unknown benchmark: '{benchmark_name}'.")

        items = self.benchmarks[benchmark_name].filewise_metrics

        if items is None or not items:
            raise ValueError(f"Filewise metrics not loaded for benchmark: '{benchmark_name}'.")

        output = [item[metric_name] for item in items if metric_name in item]

        if not output:
            raise ValueError(f"Unknown or empty metric '{metric_name}' for benchmark '{benchmark_name}'.")

        return output

    def aggregate_metric_stats(self, metric_name: str) -> list[float]:
        if any(self.benchmarks[n].filewise_metrics is None for n in self.benchmarks):
            raise ValueError("Not all benchmarks contain filewise metrics.")

        output = []

        for benchmark_name in self.benchmarks:
            for item in self.benchmarks[benchmark_name].filewise_metrics:
                if metric_name not in item:
                    continue
                output.append(item[metric_name])

        if not output:
            raise ValueError(f"Unknown or empty aggregated metric '{metric_name}'.")

        return output

    def get_benchmark_audio_paths(self, benchmark_name: str) -> dict[str, Path]:
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Unknown benchmark: '{benchmark_name}'.")

        paths = self.benchmarks[benchmark_name].generated_audio_paths

        if not paths:
            raise ValueError(f"Audio paths not loaded for benchmark: '{benchmark_name}'.")

        return paths

    def get_benchmark_sample_meta(self, benchmark_name: str) -> dict[str, _BenchmarkSampleMeta]:
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Unknown benchmark: '{benchmark_name}'.")

        items = self.benchmarks[benchmark_name].filewise_metrics

        if not items:
            raise ValueError(f"Filewise metrics not loaded for benchmark: '{benchmark_name}'.")

        output = {}

        for item in items:
            meta = _BenchmarkSampleMeta.from_filewise_metrics_item(item)
            output[meta.name] = meta

        return output


@dataclass(frozen=True)
class _ExpirationInfo:
    timestamp: int
    path_str: str
    user_str: str


def _make_expiration_info(expires_in: int) -> _ExpirationInfo:
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    return _ExpirationInfo(
        timestamp=int(expires_at.timestamp()),
        path_str=expires_at.strftime("%Y-%m-%dT%H-%M-%SZ"),
        user_str=expires_at.strftime("%Y-%m-%d %H:%M UTC"),
    )


@dataclass
class _S3Config:
    bucket: str
    endpoint_url: str
    region_name: str
    connect_timeout: int = 10


class _S3Client:
    def __init__(
        self,
        cfg: _S3Config,
        aws_access_key_id: str,
        aws_secret_access_key: str,
    ) -> None:
        self.cfg = cfg
        self.client = boto3.client(
            "s3",
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=cfg.region_name,
            config=Config(connect_timeout=cfg.connect_timeout),
        )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        expires_in: int,
        content_type: Optional[str] = None,
    ) -> str:
        kwargs = {
            "Fileobj": fileobj,
            "Bucket": self.cfg.bucket,
            "Key": key,
        }

        if content_type is not None:
            kwargs["ExtraArgs"] = {"ContentType": content_type}

        self.client.upload_fileobj(**kwargs)

        return self.get_presigned_url(key, expires_in)

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        expires_in: int,
        content_type: Optional[str] = None,
    ) -> str:
        extra_args = {}

        if content_type is not None:
            extra_args["ContentType"] = content_type

        self.client.put_object(
            Bucket=self.cfg.bucket,
            Key=key,
            Body=data,
            **extra_args,
        )

        return self.get_presigned_url(key, expires_in)

    def get_presigned_url(
        self,
        key: str,
        expires_in: int,
    ) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.cfg.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def close(self) -> None:
        self.client.close()

    def get_url(self, key: str) -> str:
        return f"{self.cfg.endpoint_url}/{self.cfg.bucket}/{key}"


def _metric_comparator(
    a: float,
    b: float,
    lower_is_better: Optional[bool],
) -> Optional[bool]:
    if lower_is_better is None:
        return None

    if lower_is_better:
        return a <= b

    return a >= b


def _format_metric_values(
    a: float,
    b: float,
    metric: _MetricSpec,
) -> tuple[str, str]:
    a, b = metric.multiplier * a, metric.multiplier * b
    a_is_better = _metric_comparator(a, b, metric.lower_is_better)
    a, b = round(a, metric.round_digits), round(b, metric.round_digits)
    a_str, b_str = f"{a}{metric.units}", f"{b}{metric.units}"

    if metric.lower_is_better is not None:
        if a_is_better:
            a_str = f"**{a_str}**"
        else:
            b_str = f"**{b_str}**"

    return a_str, b_str


def _generate_benchmark_metrics_block(
    benchmark_name: str,
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
) -> str:
    parts = []
    parts.append("\n#### Metrics")
    parts.append(f"| Metric | {bucket_baseline.name} | {bucket_candidate.name} |")
    parts.append("|---|---|---|")

    for metric in _METRICS:
        a = bucket_baseline.get_metric_avg_value(benchmark_name, metric.name)
        b = bucket_candidate.get_metric_avg_value(benchmark_name, metric.name)

        if a is None or b is None:
            if metric.optional:
                continue
            raise ValueError(f"Unknown metric '{metric.name}' for benchmark '{benchmark_name}'.")

        a_str, b_str = _format_metric_values(a, b, metric)

        parts.append(f"| {metric.report_name} | {a_str} | {b_str} |")

    return "\n".join(parts)


def _perform_stat_test(
    baseline: list[float],
    candidate: list[float],
    lower_is_better: bool,
) -> tuple[_Winner, _Alternative, float]:
    if not baseline:
        raise ValueError("Baseline sample is empty.")

    if not candidate:
        raise ValueError("Candidate sample is empty.")

    if len(baseline) != len(candidate):
        LOGGER.warning(
            "\nWARNING: Baseline and candidate contain different numbers of samples. "
            "This may indicate missing filewise metrics or dataset mismatch."
        )

    # First test whether distributions differ at all, then determine direction.
    p_val_two_sided = mannwhitneyu(baseline, candidate, alternative="two-sided", method="auto").pvalue

    if p_val_two_sided >= _SIGNIFICANCE_LEVEL:
        return _Winner.tie, _Alternative.two_sided, round(p_val_two_sided, _P_VAL_ROUND_DIGITS)

    p_val = mannwhitneyu(baseline, candidate, alternative="less", method="auto").pvalue

    if p_val < _SIGNIFICANCE_LEVEL:
        winner = _Winner.baseline if lower_is_better else _Winner.candidate
        p_val = round(p_val, _P_VAL_ROUND_DIGITS)
        return winner, _Alternative.less, p_val

    p_val = mannwhitneyu(baseline, candidate, alternative="greater", method="auto").pvalue

    if p_val < _SIGNIFICANCE_LEVEL:
        winner = _Winner.candidate if lower_is_better else _Winner.baseline
        p_val = round(p_val, _P_VAL_ROUND_DIGITS)
        return winner, _Alternative.greater, p_val

    return _Winner.tie, _Alternative.two_sided, round(p_val_two_sided, _P_VAL_ROUND_DIGITS)


def _map_winner_to_name(
    winner: _Winner,
    baseline_name: str,
    candidate_name: str,
) -> str:
    if winner == _Winner.baseline:
        return baseline_name
    if winner == _Winner.candidate:
        return candidate_name
    return winner.value


@dataclass
class _StatTestResult:
    metric_name: str
    winner: str
    alternative: str
    p_value: float


def _perform_benchmark_stat_tests(
    benchmark_name: str,
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
) -> list[_StatTestResult]:
    results = []

    for metric in _STAT_TEST_METRICS:
        winner, alternative, p_value = _perform_stat_test(
            baseline=bucket_baseline.get_metric_stats(benchmark_name, metric.name),
            candidate=bucket_candidate.get_metric_stats(benchmark_name, metric.name),
            lower_is_better=metric.lower_is_better,
        )
        winner_str = _map_winner_to_name(winner, bucket_baseline.name, bucket_candidate.name)

        result = _StatTestResult(
            metric_name=metric.report_name,
            winner=winner_str,
            alternative=alternative.value,
            p_value=p_value,
        )
        results.append(result)

    return results


def _perform_summary_stat_tests(
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
) -> list[_StatTestResult]:
    results = []

    for metric in _STAT_TEST_METRICS:
        winner, alternative, p_value = _perform_stat_test(
            baseline=bucket_baseline.aggregate_metric_stats(metric.name),
            candidate=bucket_candidate.aggregate_metric_stats(metric.name),
            lower_is_better=metric.lower_is_better,
        )
        winner_str = _map_winner_to_name(winner, bucket_baseline.name, bucket_candidate.name)

        result = _StatTestResult(
            metric_name=metric.report_name,
            winner=winner_str,
            alternative=alternative.value,
            p_value=p_value,
        )
        results.append(result)

    return results


def _generate_stat_tests_block(
    stat_test_results: list[_StatTestResult],
    comment: Optional[str] = None,
) -> str:
    title = "Statistical Tests"

    if comment is not None:
        title = title + f" ({comment})"

    parts = []
    parts.append(f"\n#### {title}")
    parts.append(f"| Metric | Winner | Alternative | p-value |")
    parts.append("|---|---|---|---|")

    for res in stat_test_results:
        parts.append(f"| {res.metric_name} | {res.winner} | {res.alternative} | {res.p_value} |")

    return "\n".join(parts)


def _generate_summary_metrics_block(
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
) -> str:
    parts = []
    parts.append("\n#### Metrics (macro-average across benchmarks)")
    parts.append(f"| Metric | {bucket_baseline.name} | {bucket_candidate.name} |")
    parts.append("|---|---|---|")

    for metric in _METRICS:
        if not metric.include_in_summary:
            continue

        a_vals, b_vals = [], []
        skip = False

        for benchmark_name in sorted(bucket_baseline.benchmarks.keys()):
            a = bucket_baseline.get_metric_avg_value(benchmark_name, metric.name)
            b = bucket_candidate.get_metric_avg_value(benchmark_name, metric.name)

            if a is None or b is None:
                if metric.optional:
                    skip = True
                    break
                raise ValueError(f"Unknown metric '{metric.name}' for benchmark '{benchmark_name}'.")

            a_vals.append(a)
            b_vals.append(b)

        if skip:
            continue

        avg_a, avg_b = np.mean(a_vals), np.mean(b_vals)
        a_str, b_str = _format_metric_values(avg_a, avg_b, metric)

        parts.append(f"| {metric.report_name} | {a_str} | {b_str} |")

    return "\n".join(parts)


def _generate_analysis_block(
    baseline_name: str,
    candidate_name: str,
    stat_test_results: list[_StatTestResult],
) -> str:
    parts = []
    parts.append("\n#### Analysis of Statistical Tests")
    a_wins, b_wins = [], []

    for res in stat_test_results:
        if res.winner == baseline_name:
            a_wins.append(res.metric_name)
        elif res.winner == candidate_name:
            b_wins.append(res.metric_name)

    if not a_wins and not b_wins:
        parts.append("No statistically significant difference was observed between these two models.")
    else:
        best_model, advantages = (baseline_name, a_wins) if len(a_wins) >= len(b_wins) else (candidate_name, b_wins)
        msg = ", ".join(advantages)
        parts.append(f"**{best_model}** performs best. Key statistically significant advantages: {msg}.")

    return "\n".join(parts)


def _generate_eval_report(
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
    task_id: str,
) -> str:
    baseline_name = bucket_baseline.name
    candidate_name = bucket_candidate.name
    parts = []
    parts.append(f"# {task_id}: TTS Evaluation Comparison Report\n")
    parts.append(f"Comparing baseline **{baseline_name}** against candidate **{candidate_name}**.\n")

    parts.append("## Summary (Aggregated Across Test Sets)\n")

    block = _generate_summary_metrics_block(bucket_baseline, bucket_candidate)
    parts.append(block)

    stat_test_results = _perform_summary_stat_tests(bucket_baseline, bucket_candidate)
    comment = "pooled filewise across benchmarks"
    block = _generate_stat_tests_block(stat_test_results, comment)
    parts.append(block)

    block = _generate_analysis_block(baseline_name, candidate_name, stat_test_results)
    parts.append(block)

    parts.append("\n## Per-Test-Set Results")

    for benchmark_name in sorted(bucket_baseline.benchmarks.keys()):
        parts.append(f"\n### {benchmark_name}\n")
        block = _generate_benchmark_metrics_block(benchmark_name, bucket_baseline, bucket_candidate)
        parts.append(block)

        stat_test_results = _perform_benchmark_stat_tests(benchmark_name, bucket_baseline, bucket_candidate)
        block = _generate_stat_tests_block(stat_test_results)
        parts.append(block)

        block = _generate_analysis_block(baseline_name, candidate_name, stat_test_results)
        parts.append(block)

    parts.append("\n---\n*Lower WER/CER is better, higher UTMOS/SSIM is better. **bold** = best value.*")

    return "\n".join(parts)


@dataclass(frozen=True)
class _AudioPair:
    baseline_path: Path
    candidate_path: Path
    text: str


def _collect_audio_pairs(
    benchmark_name: str,
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
) -> list[_AudioPair]:
    baseline_paths = bucket_baseline.get_benchmark_audio_paths(benchmark_name)
    candidate_paths = bucket_candidate.get_benchmark_audio_paths(benchmark_name)
    baseline_meta = bucket_baseline.get_benchmark_sample_meta(benchmark_name)
    candidate_meta = bucket_candidate.get_benchmark_sample_meta(benchmark_name)
    pairs = []

    if set(baseline_paths) != set(candidate_paths):
        raise ValueError(f"Audio sample sets differ for benchmark '{benchmark_name}'.")

    for name in baseline_paths:
        if name not in candidate_paths or name not in baseline_meta or name not in candidate_meta:
            raise ValueError(
                f"Missing matched sample '{name}' in candidate audio paths or metadata for benchmark '{benchmark_name}'."
            )

        if baseline_meta[name].sample_id != candidate_meta[name].sample_id:
            raise ValueError(
                f"Sample id mismatch for '{name}' in benchmark '{benchmark_name}'. "
                "Probably you use different versions of buckets."
            )

        pair = _AudioPair(
            baseline_path=baseline_paths[name],
            candidate_path=candidate_paths[name],
            text=baseline_meta[name].text,
        )
        pairs.append(pair)

    return pairs


def _sample_audio_pairs(
    pairs: list[_AudioPair],
    samples_per_benchmark: int,
) -> list[_AudioPair]:
    length = len(pairs)
    indexes = list(range(length))
    random.shuffle(indexes)
    indexes = indexes[:samples_per_benchmark]
    return [pairs[i] for i in indexes]


def _make_audio_report_header(
    task_id: str,
    comment: Optional[str] = None,
    expiration_comment: Optional[str] = None,
) -> list[str]:
    parts = []
    parts.append(_AUDIO_REPORT_HEADER_BLOCK)
    title = f"{task_id}: Audio Comparison Report"
    parts.append(f'<h1>{html.escape(title)}</h1>\n')

    if expiration_comment is not None:
        parts.append(f'<p class="expiration_comment">{html.escape(expiration_comment)}</p>\n')

    if comment is not None:
        parts.append(f'<p class="comment">{html.escape(comment)}</p>\n')

    return parts


def _append_audio_pair_block(
    parts: list[str],
    baseline_name: str,
    candidate_name: str,
    baseline_audio: str,
    candidate_audio: str,
    text: str,
    show_model_names: bool,
) -> None:
    baseline_audio = html.escape(baseline_audio, quote=True)
    candidate_audio = html.escape(candidate_audio, quote=True)
    text = html.escape(text)

    parts.append('<div class="pair-row">')

    parts.append('<div class="audio-box">')
    if show_model_names:
        parts.append(f"<strong>{html.escape(baseline_name)}</strong><br><br>")
    parts.append(f'<audio controls><source src="{baseline_audio}" type="audio/wav"></audio></div>')

    parts.append('<div class="audio-box">')
    if show_model_names:
        parts.append(f"<strong>{html.escape(candidate_name)}</strong><br><br>")
    parts.append(f'<audio controls><source src="{candidate_audio}" type="audio/wav"></audio></div>')

    parts.append("</div>")
    parts.append(f'<p class="pair-comment">Text: {text}</p>\n')


def _encode_audio_bytes(data: bytes) -> str:
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:audio/wav;base64,{b64}"


def _make_audio_report_local(
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
    task_id: str,
    used_benchmarks: list[str],
    samples_per_benchmark: int,
    comment: Optional[str],
    storage: _Storage,
) -> str:
    pbar = tqdm(total=len(used_benchmarks) * samples_per_benchmark, ncols=_TQDM_NCOLS)
    parts = _make_audio_report_header(task_id=task_id, comment=comment)

    for benchmark_name in used_benchmarks:
        pairs = _collect_audio_pairs(benchmark_name, bucket_baseline, bucket_candidate)
        sampled_pairs = _sample_audio_pairs(pairs, samples_per_benchmark)

        if len(sampled_pairs) < samples_per_benchmark:
            LOGGER.warning(
                f"\nWARNING: Benchmark '{benchmark_name}' contains only {len(sampled_pairs)} available paired samples, "
                f"but {samples_per_benchmark} were requested."
            )

        parts.append(f"<br><h2>{html.escape(benchmark_name)}</h2>\n")

        for i, pair in enumerate(sampled_pairs):
            baseline_bytes = storage.read_bytes(pair.baseline_path)
            candidate_bytes = storage.read_bytes(pair.candidate_path)
            baseline_audio = _encode_audio_bytes(baseline_bytes)
            candidate_audio = _encode_audio_bytes(candidate_bytes)

            _append_audio_pair_block(
                parts=parts,
                baseline_name=bucket_baseline.name,
                candidate_name=bucket_candidate.name,
                baseline_audio=baseline_audio,
                candidate_audio=candidate_audio,
                text=pair.text,
                show_model_names=(i == 0),
            )
            pbar.update(1)

        missing = samples_per_benchmark - len(sampled_pairs)
        if missing > 0:
            pbar.update(missing)

    parts.append("</body></html>")
    pbar.close()

    return "".join(parts)


def _make_audio_report_s3(
    bucket_baseline: _BucketData,
    bucket_candidate: _BucketData,
    task_id: str,
    used_benchmarks: list[str],
    samples_per_benchmark: int,
    comment: Optional[str],
    storage: _Storage,
    s3_client: _S3Client,
    s3_prefix: str,
) -> str:
    expiration_info = _make_expiration_info(_S3_LINK_EXPIRES_IN)
    report_path_prefix = f"{s3_prefix}-{expiration_info.path_str}"

    expiration_comment = f"Audio links for this report will expire at {expiration_info.user_str}"

    pbar = tqdm(total=len(used_benchmarks) * samples_per_benchmark, ncols=_TQDM_NCOLS)
    parts = _make_audio_report_header(
        task_id=task_id,
        comment=comment,
        expiration_comment=expiration_comment,
    )

    for benchmark_name in used_benchmarks:
        pairs = _collect_audio_pairs(benchmark_name, bucket_baseline, bucket_candidate)
        sampled_pairs = _sample_audio_pairs(pairs, samples_per_benchmark)

        if len(sampled_pairs) < samples_per_benchmark:
            LOGGER.warning(
                f"\nWARNING: Benchmark '{benchmark_name}' contains only {len(sampled_pairs)} available paired samples, "
                f"but {samples_per_benchmark} were requested."
            )

        parts.append(f"<br><h2>{html.escape(benchmark_name)}</h2>\n")

        for i, pair in enumerate(sampled_pairs):
            with storage.open_file(pair.baseline_path) as f:
                baseline_audio = s3_client.upload_fileobj(
                    fileobj=f,
                    key=f"{report_path_prefix}/audio/baseline_{benchmark_name}_{i}.wav",
                    expires_in=_S3_LINK_EXPIRES_IN,
                    content_type="audio/wav",
                )
            with storage.open_file(pair.candidate_path) as f:
                candidate_audio = s3_client.upload_fileobj(
                    fileobj=f,
                    key=f"{report_path_prefix}/audio/candidate_{benchmark_name}_{i}.wav",
                    expires_in=_S3_LINK_EXPIRES_IN,
                    content_type="audio/wav",
                )
            _append_audio_pair_block(
                parts=parts,
                baseline_name=bucket_baseline.name,
                candidate_name=bucket_candidate.name,
                baseline_audio=baseline_audio,
                candidate_audio=candidate_audio,
                text=pair.text,
                show_model_names=(i == 0),
            )
            pbar.update(1)

        missing = samples_per_benchmark - len(sampled_pairs)
        if missing > 0:
            pbar.update(missing)

    parts.append("</body></html>")
    pbar.close()

    report = "".join(parts)

    report_url = s3_client.upload_bytes(
        data=report.encode("utf-8"),
        key=f"{report_path_prefix}/report.html",
        expires_in=_S3_LINK_EXPIRES_IN,
        content_type="text/html; charset=utf-8",
    )
    data_url = s3_client.get_url(report_path_prefix)
    LOGGER.info(f"\nAudio report data uploaded to {data_url}")

    return report_url


def _generate_reports(
    baseline_name: str,
    candidate_name: str,
    baseline_path: Path,
    candidate_path: Path,
    generate_audio_report: bool,
    upload_audio_report_to_s3: bool,
    audio_report_benchmarks: Optional[list[str]],
    samples_per_benchmark: int,
    audio_report_comment: Optional[str],
    task_id: str,
    bucket_structure: _BucketStructure,
    storage: _Storage,
    s3_client: Optional[_S3Client],
) -> tuple[str, Optional[str], Optional[str]]:
    audio_report: Optional[str] = None
    audio_report_url: Optional[str] = None

    LOGGER.info(f"\nLoading metadata for {baseline_name}...")
    bucket_baseline = _BucketData.from_storage(
        bucket_name=baseline_name,
        bucket_path=baseline_path,
        bucket_structure=bucket_structure,
        check_audio=generate_audio_report,
        storage=storage,
    )
    LOGGER.info(f"Loading metadata for {candidate_name}...")
    bucket_candidate = _BucketData.from_storage(
        bucket_name=candidate_name,
        bucket_path=candidate_path,
        bucket_structure=bucket_structure,
        check_audio=generate_audio_report,
        storage=storage,
    )

    baseline_set = set(bucket_baseline.benchmarks.keys())
    candidate_set = set(bucket_candidate.benchmarks.keys())

    if baseline_set != candidate_set:
        raise ValueError(f"Benchmark sets differ: '{baseline_set}' vs '{candidate_set}'.")

    LOGGER.info(f"\nLoading metric data for {baseline_name}:")
    bucket_baseline.load_metrics(storage)

    LOGGER.info(f"\nLoading metric data for {candidate_name}:")
    bucket_candidate.load_metrics(storage)

    LOGGER.info("\nPreparing evaluation report...")
    eval_report = _generate_eval_report(
        bucket_baseline=bucket_baseline,
        bucket_candidate=bucket_candidate,
        task_id=task_id,
    )
    if generate_audio_report:
        LOGGER.info("\nPreparing audio report...")

        if audio_report_benchmarks is None:
            raise ValueError("Audio report benchmarks must be provided when audio report is enabled.")

        if upload_audio_report_to_s3:
            if s3_client is None:
                raise ValueError("S3 client must be provided when uploading audio report to S3.")

            s3_prefix = _generate_report_name(baseline_path, candidate_path, task_id)

            audio_report_url = _make_audio_report_s3(
                bucket_baseline=bucket_baseline,
                bucket_candidate=bucket_candidate,
                task_id=task_id,
                used_benchmarks=audio_report_benchmarks,
                samples_per_benchmark=samples_per_benchmark,
                comment=audio_report_comment,
                storage=storage,
                s3_client=s3_client,
                s3_prefix=s3_prefix,
            )
        else:
            audio_report = _make_audio_report_local(
                bucket_baseline=bucket_baseline,
                bucket_candidate=bucket_candidate,
                task_id=task_id,
                used_benchmarks=audio_report_benchmarks,
                samples_per_benchmark=samples_per_benchmark,
                comment=audio_report_comment,
                storage=storage,
            )

    return eval_report, audio_report, audio_report_url


def _generate_report_name(
    baseline_path: Path,
    candidate_path: Path,
    task_id: str,
) -> str:
    return f"{task_id}-{baseline_path.stem}_vs_{candidate_path.stem}"


def _save_reports(
    save_path: Path,
    eval_report: str,
    audio_report: Optional[str],
    baseline_path: Path,
    candidate_path: Path,
    task_id: str,
) -> None:
    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)

    name = _generate_report_name(baseline_path, candidate_path, task_id)
    eval_report_save_path = save_path / f"{name}.md"

    with open(eval_report_save_path, "w", encoding="utf-8") as f:
        f.write(eval_report)

    LOGGER.info(f"\nSaved eval report to {eval_report_save_path.as_posix()}")

    if audio_report is not None:
        audio_report_save_path = save_path / f"{name}.html"

        with open(audio_report_save_path, "w", encoding="utf-8") as f:
            f.write(audio_report)

        LOGGER.info(f"Saved audio report to {audio_report_save_path.as_posix()}\n")


def _create_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Script for generating MagpieTTS evaluation comparison reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--baseline_name",
        type=str,
        required=True,
        help="Name of the baseline model that will be used in report.",
    )
    parser.add_argument(
        "--baseline_path",
        type=str,
        required=True,
        help="Path to the generated evaluation bucket for the baseline model.",
    )
    parser.add_argument(
        "--candidate_name",
        type=str,
        required=True,
        help="Name of the candidate model that will be used in report.",
    )
    parser.add_argument(
        "--candidate_path",
        type=str,
        required=True,
        help="Path to the generated evaluation bucket for the candidate model.",
    )
    parser.add_argument(
        "--remote_hostname",
        type=str,
        default=None,
        help="Name of the remote host, if the generated buckets are located there.",
    )
    parser.add_argument(
        "--remote_username",
        type=str,
        default=None,
        help="Name of the user on the remote host.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./",
        help="Output directory for generated reports.",
    )
    parser.add_argument(
        "--task_id",
        type=str,
        default=_DUMMY_TASK_ID,
        help="Jira task number associated with this report.",
    )
    parser.add_argument(
        "--results_subdir",
        type=str,
        default="results",
        help="Subdirectory inside the bucket root that contains evaluation outputs produced by `magpietts_inference`.",
    )
    parser.add_argument(
        "--audio_report",
        action='store_true',
        help="Generate additional report with side-by-side audio comparison.",
    )
    parser.add_argument(
        "--audio_report_benchmarks",
        type=str,
        default="libritts_test_clean,riva_hard_digits,riva_hard_letters",
        help="Comma-separated list of benchmarks to include in the audio report.",
    )
    parser.add_argument(
        "--samples_per_benchmark",
        type=int,
        default=30,
        help="Number of samples per benchmark in the audio report.",
    )
    parser.add_argument(
        "--audio_report_comment",
        type=str,
        default=None,
        help="Comment used in the audio report to describe the configuration.",
    )
    parser.add_argument(
        "--upload_audio_report_to_s3",
        action='store_true',
        help="Upload the audio report HTML and referenced audio files to S3 instead of saving a local HTML report.",
    )
    parser.add_argument(
        "--s3_endpoint",
        type=str,
        default=None,
        help="S3 endpoint URL used for uploading the audio report.",
    )
    parser.add_argument(
        "--s3_bucket",
        type=str,
        default=None,
        help="Name of the S3 bucket where the audio report HTML and audio files will be uploaded.",
    )
    parser.add_argument(
        "--s3_region",
        type=str,
        default=None,
        help="AWS region name for the S3 client.",
    )
    return parser


def main() -> None:
    """Run the CLI entry point for generating evaluation and optional audio comparison reports."""
    parser = _create_argparser()
    args = parser.parse_args()

    bucket_structure = _BucketStructure()
    bucket_structure.eval_output_subdir = args.results_subdir
    baseline_path = Path(args.baseline_path)
    candidate_path = Path(args.candidate_path)
    task_id = args.task_id

    storage: _Storage
    ssh_client: Optional[SSHClient] = None
    sftp: Optional[SFTPClient] = None
    s3_cfg: Optional[_S3Config] = None
    s3_client: Optional[_S3Client] = None
    eval_report: Optional[str] = None
    audio_report: Optional[str] = None
    audio_report_url: Optional[str] = None
    audio_report_benchmarks: Optional[list[str]] = None

    if args.upload_audio_report_to_s3 and not args.audio_report:
        raise ValueError("'--upload_audio_report_to_s3' requires '--audio_report'.")

    if args.audio_report:
        audio_report_benchmarks = [x.strip() for x in args.audio_report_benchmarks.split(",") if x.strip()]
        for name in audio_report_benchmarks:
            if name not in _BENCHMARK_NAMES:
                raise ValueError(f"Unknown benchmark name: '{name}'.")

        if not audio_report_benchmarks:
            raise ValueError("Empty list of benchmark names was provided for the audio report.")

        if args.samples_per_benchmark <= 0:
            raise ValueError("Number of samples per benchmark for the audio report must be greater than 0.")

        if args.upload_audio_report_to_s3:
            if args.s3_bucket is None:
                raise ValueError("'--s3_bucket' must be provided when '--upload_audio_report_to_s3' is used.")

            if args.s3_endpoint is None:
                raise ValueError("'--s3_endpoint' must be provided when '--upload_audio_report_to_s3' is used.")

            if args.s3_region is None:
                raise ValueError("'--s3_region' must be provided when '--upload_audio_report_to_s3' is used.")

            _s3_key_id = os.getenv(_S3_ACCESS_KEY_ID)
            _s3_key = os.getenv(_S3_SECRET_ACCESS_KEY)

            if _s3_key_id is None or _s3_key is None:
                raise ValueError(
                    f"Environment variables '{_S3_ACCESS_KEY_ID}' and '{_S3_SECRET_ACCESS_KEY}' "
                    "must be set when uploading audio report to S3."
                )

            s3_cfg = _S3Config(
                bucket=args.s3_bucket,
                endpoint_url=args.s3_endpoint,
                region_name=args.s3_region,
            )
            s3_client = _S3Client(
                cfg=s3_cfg,
                aws_access_key_id=_s3_key_id,
                aws_secret_access_key=_s3_key,
            )

    if task_id == _DUMMY_TASK_ID:
        LOGGER.warning("\nWARNING: It is recommended to assign the evaluation report to a specific ticket!")

    LOGGER.info(f"\nComparing baseline '{args.baseline_name}' against candidate '{args.candidate_name}'")

    try:
        if args.remote_hostname is not None or args.remote_username is not None:
            if args.remote_username is None:
                raise ValueError("'remote_username' must be provided when using remote access.")

            if args.remote_hostname is None:
                raise ValueError("'remote_hostname' must be provided when using remote access.")

            _host_key = os.getenv(_REMOTE_HOST_KEY)

            if _host_key is None:
                raise ValueError(f"Environment variable '{_REMOTE_HOST_KEY}' is not set.")

            LOGGER.info(f"\nSetting remote connection with host: {args.remote_hostname}")

            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.connect(
                hostname=args.remote_hostname,
                username=args.remote_username,
                password=_host_key,
            )
            sftp = ssh_client.open_sftp()
            storage = _SFTPStorage(sftp)

        else:
            storage = _LocalStorage()

        eval_report, audio_report, audio_report_url = _generate_reports(
            baseline_name=args.baseline_name,
            candidate_name=args.candidate_name,
            baseline_path=baseline_path,
            candidate_path=candidate_path,
            generate_audio_report=args.audio_report,
            upload_audio_report_to_s3=args.upload_audio_report_to_s3,
            audio_report_benchmarks=audio_report_benchmarks,
            samples_per_benchmark=args.samples_per_benchmark,
            audio_report_comment=args.audio_report_comment,
            task_id=task_id,
            bucket_structure=bucket_structure,
            storage=storage,
            s3_client=s3_client,
        )

    finally:
        if sftp is not None:
            sftp.close()

        if ssh_client is not None:
            ssh_client.close()

        if s3_client is not None:
            s3_client.close()

    if eval_report is None:
        raise RuntimeError("Failed to generate evaluation report.")

    if args.audio_report and not args.upload_audio_report_to_s3 and audio_report is None:
        raise RuntimeError("Failed to generate audio report.")

    if args.audio_report and args.upload_audio_report_to_s3 and audio_report_url is None:
        raise RuntimeError("Failed to upload audio report to S3 and create URL.")

    _save_reports(
        save_path=Path(args.output_dir),
        eval_report=eval_report,
        audio_report=audio_report,
        baseline_path=baseline_path,
        candidate_path=candidate_path,
        task_id=task_id,
    )

    if audio_report_url is not None:
        LOGGER.info(
            f"\nAudio report is available at:\n\n{audio_report_url}\n\nSave the link and open it in your browser!\n"
        )


if __name__ == "__main__":
    main()
