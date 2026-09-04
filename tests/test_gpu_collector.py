import pytest

from app.resources.gpu_collector import GPUResourceCollector


SAMPLE_DCGM_METRICS = """
# HELP DCGM_FI_DEV_FB_FREE Framebuffer memory free (in MiB).
# TYPE DCGM_FI_DEV_FB_FREE gauge
DCGM_FI_DEV_FB_FREE{gpu="0",UUID="GPU-test",pci_bus_id="0000",device="nvidia0",modelName="Tesla T4"} 1493
# HELP DCGM_FI_DEV_FB_USED Framebuffer memory used (in MiB).
# TYPE DCGM_FI_DEV_FB_USED gauge
DCGM_FI_DEV_FB_USED{gpu="0",UUID="GPU-test",pci_bus_id="0000",device="nvidia0",modelName="Tesla T4"} 13418
# HELP DCGM_FI_DEV_GPU_UTIL GPU utilization (in %).
# TYPE DCGM_FI_DEV_GPU_UTIL gauge
DCGM_FI_DEV_GPU_UTIL{gpu="0",UUID="GPU-test",pci_bus_id="0000",device="nvidia0",modelName="Tesla T4"} 0
# HELP DCGM_FI_DEV_MEM_COPY_UTIL Memory utilization (in %).
# TYPE DCGM_FI_DEV_MEM_COPY_UTIL gauge
DCGM_FI_DEV_MEM_COPY_UTIL{gpu="0",UUID="GPU-test",pci_bus_id="0000",device="nvidia0",modelName="Tesla T4"} 0
"""


def test_parse_dcgmi_metrics():
    state = GPUResourceCollector._parse_metrics(
        SAMPLE_DCGM_METRICS
    )

    assert state["gpu_name"] == "Tesla T4"
    assert state["gpu_utilization_percent"] == 0.0
    assert state["memory_utilization_percent"] == 0.0
    assert state["memory_total_mib"] == 15360.0
    assert state["memory_used_mib"] == 13418.0
    assert state["memory_free_mib"] == 1493.0


def test_parse_labels():
    labels = GPUResourceCollector._parse_labels(
        'gpu="0",modelName="Tesla T4",device="nvidia0"'
    )

    assert labels["gpu"] == "0"
    assert labels["modelName"] == "Tesla T4"
    assert labels["device"] == "nvidia0"


def test_missing_required_metric_is_rejected():
    incomplete = """
DCGM_FI_DEV_GPU_UTIL{gpu="0",modelName="Tesla T4"} 0
"""

    with pytest.raises(RuntimeError, match="Missing required DCGM metrics"):
        GPUResourceCollector._parse_metrics(incomplete)
