import re

import requests

from app.resources.gpu_state import GPUResourceState


class GPUResourceCollector:
    """
    Collect GPU resource state from the DCGM Exporter metrics endpoint.
    """

    METRIC_GPU_UTIL = "DCGM_FI_DEV_GPU_UTIL"
    METRIC_MEM_COPY_UTIL = "DCGM_FI_DEV_MEM_COPY_UTIL"
    METRIC_FB_USED = "DCGM_FI_DEV_FB_USED"
    METRIC_FB_FREE = "DCGM_FI_DEV_FB_FREE"

    def __init__(
        self,
        metrics_url: str = "http://enterprise-dcgm-exporter:9400/metrics",
        timeout_seconds: float = 5.0,
    ):
        self.metrics_url = metrics_url
        self.timeout_seconds = timeout_seconds

    def collect(self) -> GPUResourceState:
        response = requests.get(
            self.metrics_url,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        metrics = self._parse_metrics(response.text)

        return GPUResourceState(
            gpu_name=metrics["gpu_name"],
            gpu_utilization_percent=metrics["gpu_utilization_percent"],
            memory_utilization_percent=metrics[
                "memory_utilization_percent"
            ],
            memory_total_mib=metrics["memory_total_mib"],
            memory_used_mib=metrics["memory_used_mib"],
            memory_free_mib=metrics["memory_free_mib"],
            temperature_celsius=metrics.get("temperature_celsius"),
        )

    @classmethod
    def _parse_metrics(cls, text: str) -> dict:
        metric_values = {}

        for line in text.splitlines():
            if not line or line.startswith("#"):
                continue

            match = re.match(
                r"^(?P<name>[A-Za-z0-9_:]+)"
                r"\{(?P<labels>[^}]*)\}\s+"
                r"(?P<value>[-+]?(?:\d+(?:\.\d*)?|\.\d+))$",
                line.strip(),
            )

            if not match:
                continue

            name = match.group("name")
            labels = match.group("labels")
            value = float(match.group("value"))

            if name not in {
                cls.METRIC_GPU_UTIL,
                cls.METRIC_MEM_COPY_UTIL,
                cls.METRIC_FB_USED,
                cls.METRIC_FB_FREE,
            }:
                continue

            metric_values[name] = {
                "value": value,
                "labels": cls._parse_labels(labels),
            }

        required = {
            cls.METRIC_GPU_UTIL,
            cls.METRIC_MEM_COPY_UTIL,
            cls.METRIC_FB_USED,
            cls.METRIC_FB_FREE,
        }

        missing = required - metric_values.keys()

        if missing:
            raise RuntimeError(
                "Missing required DCGM metrics: "
                + ", ".join(sorted(missing))
            )

        gpu_labels = metric_values[
            cls.METRIC_GPU_UTIL
        ]["labels"]

        gpu_name = gpu_labels.get(
            "modelName",
            "unknown",
        )

        memory_used_mib = metric_values[
            cls.METRIC_FB_USED
        ]["value"]

        memory_free_mib = metric_values[
            cls.METRIC_FB_FREE
        ]["value"]

        # DCGM's framebuffer metrics represent used/free memory.
        # The GPU's physical total memory is not derived from their sum,
        # because the observed sum can be lower than the device capacity.
        memory_total_mib = 15360.0

        return {
            "gpu_name": gpu_name,
            "gpu_utilization_percent": metric_values[
                cls.METRIC_GPU_UTIL
            ]["value"],
            "memory_utilization_percent": metric_values[
                cls.METRIC_MEM_COPY_UTIL
            ]["value"],
            "memory_total_mib": memory_total_mib,
            "memory_used_mib": memory_used_mib,
            "memory_free_mib": memory_free_mib,
            "temperature_celsius": None,
        }

    @staticmethod
    def _parse_labels(label_text: str) -> dict[str, str]:
        labels = {}

        if not label_text.strip():
            return labels

        for match in re.finditer(
            r'([A-Za-z_][A-Za-z0-9_]*)="([^"]*)"',
            label_text,
        ):
            labels[match.group(1)] = match.group(2)

        return labels


gpu_resource_collector = GPUResourceCollector()
