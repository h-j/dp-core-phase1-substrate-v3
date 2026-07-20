"""
Phase 4: Tests for repository list serialization.
Verifies JSON serialization & backward-compatible fallback for string lists.
No database or external services required.
"""
import json
import pytest
from memory.relational.repositories.reflective_memory_repository import ReflectiveMemoryRepository
from memory.market.market_observation_repository import MarketObservationRepository


def test_reflective_memory_json_serialization_round_trip():
    repo = ReflectiveMemoryRepository()
    data = ["item 1", "item 2 with newline\nembedded", "item 3"]
    serialized = repo._serialize(data)
    assert isinstance(serialized, str)
    deserialized = repo._deserialize(serialized)
    assert deserialized == data, "JSON serialization must preserve list elements with embedded newlines"


def test_reflective_memory_legacy_newline_fallback():
    repo = ReflectiveMemoryRepository()
    legacy_str = "item1\nitem2\nitem3"
    deserialized = repo._deserialize(legacy_str)
    assert deserialized == ["item1", "item2", "item3"], "Legacy newline-delimited strings must deserialize correctly"


def test_market_observation_json_serialization_round_trip():
    repo = MarketObservationRepository()
    data = ["tag1", "tag2: detail", "tag3"]
    serialized = repo._serialize(data)
    deserialized = repo._deserialize(serialized)
    assert deserialized == data


def test_deserialize_handles_none_and_empty():
    repo = ReflectiveMemoryRepository()
    assert repo._deserialize(None) == []
    assert repo._deserialize("") == []
    assert repo._deserialize("[]") == []
