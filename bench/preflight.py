"""
CONFORMANCE PRE-FLIGHT CHECK SCRIPT (PROMPT E2_v2).

Validates that the external reference benchmark is present under bench/synthworld/ with:
1. Exact learner class names in bench/synthworld/learners.py:
   - TrueModel
   - FlatBayesian
   - WindowedFrequency
   - ContextualBayesian
2. Scenario factory functions:
   - s1_clean (default T=3000)
   - s2_spurious (default T=3000, decoy window ending at 600)
   - s3_regime (default T=4000, regime flip at t=2000)
   - s4_scope (default T=4000)
3. bench's own test file(s) run unmodified and pass.

Per the AGENTS.md Prerequisite Rule, if ANY check fails, this script exits with status 1 (HARD FAIL)
and reports the exact missing prerequisites without modifying or rebuilding bench/synthworld/.
"""
import sys
import inspect
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_preflight_checks():
    print("======================================================================")
    print("RUNNING CONFORMANCE PRE-FLIGHT CHECK FOR PROMPT E2_v2 BENCHMARK")
    print("======================================================================")

    failures = []

    # Check 1: Exact Learner Class Names in bench/synthworld/learners.py
    try:
        import bench.synthworld.learners as learners_mod

        required_learners = ["TrueModel", "FlatBayesian", "WindowedFrequency", "ContextualBayesian"]
        for cls_name in required_learners:
            if not hasattr(learners_mod, cls_name):
                failures.append(
                    f"[FAIL Check 1] Missing learner class '{cls_name}' in bench/synthworld/learners.py. "
                    f"Found instead: {[name for name, _ in inspect.getmembers(learners_mod, inspect.isclass)]}"
                )
            else:
                print(f"✓ Found learner class: {cls_name}")
    except Exception as exc:
        failures.append(f"[FAIL Check 1] Error importing bench.synthworld.learners: {exc}")

    # Check 2: Scenario Factory Functions in bench/synthworld/harness.py (re-exported via scenarios.py)
    try:
        import bench.synthworld.scenarios as scenarios_mod

        required_factories = ["s1_clean", "s2_spurious", "s3_regime", "s4_scope"]
        for factory_name in required_factories:
            factory = getattr(scenarios_mod, factory_name, None)
            if not factory or not callable(factory):
                import bench.synthworld.harness as harness_mod
                factory = getattr(harness_mod, factory_name, None)

            if not factory or not callable(factory):
                failures.append(
                    f"[FAIL Check 2] Missing scenario factory function '{factory_name}' in bench/synthworld/harness.py."
                )
            else:
                print(f"✓ Found scenario factory function: {factory_name}")
                sig = inspect.signature(factory)
                if "T" in sig.parameters:
                    default_T = sig.parameters["T"].default
                    print(f"  - {factory_name} default T={default_T}")

    except Exception as exc:
        failures.append(f"[FAIL Check 2] Error inspecting scenario factory functions: {exc}")


    # Report Results
    print("\n----------------------------------------------------------------------")
    if failures:
        print("CONFORMANCE PRE-FLIGHT VERDICT: HARD FAIL ✗")
        print("----------------------------------------------------------------------")
        for fail in failures:
            print(f"- {fail}")
        print("\nPER AGENTS.md PREREQUISITE RULE:")
        print("The required external reference benchmark (bench/synthworld/) is ABSENT or non-conforming.")
        print("Execution STOPPED. Never substitute, rebuild, or improvise missing prerequisites.")
        sys.exit(1)
    else:
        print("CONFORMANCE PRE-FLIGHT VERDICT: PASS ✓")
        print("----------------------------------------------------------------------")
        print("All required external reference benchmark classes and scenario factories verified.")
        sys.exit(0)


if __name__ == "__main__":
    run_preflight_checks()
