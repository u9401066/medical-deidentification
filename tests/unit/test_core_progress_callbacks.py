"""
Core progress callback tests.

These tests keep the UI progress contract close to the PHI processing engine:
long-text MapReduce processing must report real chunk completion events.
"""

from core.domain.phi_identification_models import PHIDetectionResponse
from core.infrastructure.rag.chains import map_reduce


class DummySplitter:
    def split_text(self, text: str) -> list[str]:
        return ["alpha patient", "beta patient"]


class DummyMapChain:
    def invoke(self, payload: dict) -> PHIDetectionResponse:
        return PHIDetectionResponse(entities=[], has_phi=False)


def test_map_reduce_emits_chunk_progress(monkeypatch):
    monkeypatch.setattr(map_reduce, "build_map_chain", lambda llm: DummyMapChain())
    events = []

    entities = map_reduce.identify_phi_with_map_reduce(
        text="alpha patient beta patient",
        llm=object(),
        text_splitter=DummySplitter(),
        language="zh-TW",
        progress_callback=events.append,
    )

    assert entities == []

    event_names = [event["event"] for event in events]
    assert event_names[0] == "chunks_prepared"
    assert event_names.count("chunk_started") == 2
    assert event_names.count("chunk_completed") == 2
    assert "reduce_started" in event_names
    assert event_names[-1] == "reduce_completed"

    completed = [event for event in events if event["event"] == "chunk_completed"]
    assert completed[0]["chunk_number"] == 1
    assert completed[0]["total_chunks"] == 2
    assert completed[0]["success"] is True
    assert completed[1]["chunk_number"] == 2
