import pytest

from app.gateway.latency import LatencyTracker


def test_records_and_calculates_average():
    tracker = LatencyTracker(window_size=3)

    tracker.record("tinyllama", 1.0)
    tracker.record("tinyllama", 2.0)
    tracker.record("tinyllama", 3.0)

    assert tracker.sample_count("tinyllama") == 3
    assert tracker.average_latency("tinyllama") == 2.0


def test_window_is_bounded():
    tracker = LatencyTracker(window_size=3)

    tracker.record("phi3", 1.0)
    tracker.record("phi3", 2.0)
    tracker.record("phi3", 3.0)
    tracker.record("phi3", 4.0)

    assert tracker.sample_count("phi3") == 3
    assert tracker.recent_samples("phi3") == (2.0, 3.0, 4.0)
    assert tracker.average_latency("phi3") == 3.0


def test_models_have_independent_history():
    tracker = LatencyTracker(window_size=3)

    tracker.record("tinyllama", 1.0)
    tracker.record("phi3", 2.0)

    assert tracker.average_latency("tinyllama") == 1.0
    assert tracker.average_latency("phi3") == 2.0


def test_unknown_model_has_no_average():
    tracker = LatencyTracker()

    assert tracker.average_latency("tinyllama") is None
    assert tracker.sample_count("tinyllama") == 0


def test_negative_latency_is_rejected():
    tracker = LatencyTracker()

    with pytest.raises(ValueError):
        tracker.record("tinyllama", -1.0)


def test_empty_model_is_rejected():
    tracker = LatencyTracker()

    with pytest.raises(ValueError):
        tracker.record("", 1.0)


def test_invalid_window_size_is_rejected():
    with pytest.raises(ValueError):
        LatencyTracker(window_size=0)
