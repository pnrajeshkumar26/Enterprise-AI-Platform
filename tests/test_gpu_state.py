from app.resources.gpu_state import GPUResourceState


def test_gpu_resource_state():
    state = GPUResourceState(
        gpu_name="Tesla T4",
        gpu_utilization_percent=0.0,
        memory_utilization_percent=0.0,
        memory_total_mib=15360.0,
        memory_used_mib=13419.0,
        memory_free_mib=1494.0,
        temperature_celsius=37.0,
    )

    assert state.gpu_name == "Tesla T4"
    assert state.gpu_utilization_percent == 0.0
    assert state.memory_utilization_percent == 0.0
    assert state.memory_total_mib == 15360.0
    assert state.memory_used_mib == 13419.0
    assert state.memory_free_mib == 1494.0
    assert state.temperature_celsius == 37.0


def test_temperature_can_be_unknown():
    state = GPUResourceState(
        gpu_name="Tesla T4",
        gpu_utilization_percent=0.0,
        memory_utilization_percent=0.0,
        memory_total_mib=15360.0,
        memory_used_mib=13419.0,
        memory_free_mib=1494.0,
    )

    assert state.temperature_celsius is None
