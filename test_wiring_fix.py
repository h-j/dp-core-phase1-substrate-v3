#!/usr/bin/env python
"""Quick test to verify wiring fixes without full replay."""

import sys
from pathlib import Path

# Test 1: Import modules
print("Testing imports...")
try:
    from market.replay.replay_engine import ReplayExecutor
    from market.replay.replay_analysis import ReplayAnalysisEngine
    from market.replay.capital_simulator import CapitalSimulator
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check that set_capital_simulation_logs method exists
print("\nTesting ReplayAnalysisEngine methods...")
engine = ReplayAnalysisEngine()

if not hasattr(engine, 'set_capital_simulation_logs'):
    print("✗ set_capital_simulation_logs method missing")
    sys.exit(1)
print("✓ set_capital_simulation_logs method exists")

if not hasattr(engine, 'set_capital_simulation_summary'):
    print("✗ set_capital_simulation_summary method missing")
    sys.exit(1)
print("✓ set_capital_simulation_summary method exists")

# Test 3: Verify capital simulator has get_daily_logs
print("\nTesting CapitalSimulator methods...")
simulator = CapitalSimulator()

if not hasattr(simulator, 'get_daily_logs'):
    print("✗ get_daily_logs method missing")
    sys.exit(1)
print("✓ get_daily_logs method exists")

# Test get_daily_logs returns a list
logs = simulator.get_daily_logs()
if not isinstance(logs, list):
    print(f"✗ get_daily_logs should return list, got {type(logs)}")
    sys.exit(1)
print(f"✓ get_daily_logs returns list (currently {len(logs)} items)")

# Test 4: Verify set_capital_simulation_logs accepts logs
print("\nTesting log transfer...")
test_logs = [{"date": "2026-05-25", "capital_after": 10000}]
try:
    engine.set_capital_simulation_logs(test_logs)
    if engine.capital_simulation_logs != test_logs:
        print("✗ capital_simulation_logs not properly set")
        sys.exit(1)
    print("✓ Logs transferred successfully")
except Exception as e:
    print(f"✗ Failed to set logs: {e}")
    sys.exit(1)

# Test 5: Verify prediction history exists
print("\nTesting prediction history...")
if not hasattr(engine, 'prediction_history'):
    print("✗ prediction_history attribute missing")
    sys.exit(1)
print(f"✓ prediction_history exists (currently {len(engine.prediction_history)} items)")

print("\n" + "="*60)
print("✓ All wiring tests passed!")
print("="*60)
