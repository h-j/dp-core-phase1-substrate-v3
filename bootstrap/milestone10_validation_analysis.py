import json
from pathlib import Path
import numpy as np
from memory.relational.postgres_client import SessionLocal
from memory.relational.models.belief_state_model import BeliefStateModel, BeliefTransitionEventModel
from memory.relational.models.validation_record_model import ValidationRecordModel
from memory.knowledge.knowledge_repository import KnowledgeRepository

def analyze_learning_dynamics():
    kr = KnowledgeRepository()

    with SessionLocal() as session:
        # Part 1: BeliefStates and trajectories
        beliefs = session.query(BeliefStateModel).all()
        print("=== PART 1: BELIEF STATES ===")
        print(f"Total Beliefs Created: {len(beliefs)}")
        
        # We query all events to trace trajectory
        events = session.query(BeliefTransitionEventModel).order_by(BeliefTransitionEventModel.created_at.asc()).all()
        print(f"Total Belief Transition Events Logged: {len(events)}")

        # Group events by lineage
        lineage_events = {}
        for ev in events:
            lineage_events.setdefault(ev.lineage_id, []).append(ev)

        for lineage_id, evs in lineage_events.items():
            print(f"\nLineage: {lineage_id}")
            conf_traj = [e.confidence_after for e in evs]
            unc_traj = [e.uncertainty_after for e in evs]
            print(f"  Confidence trajectory (first 5): {conf_traj[:5]}")
            print(f"  Confidence trajectory (last 5): {conf_traj[-5:]}")
            print(f"  Uncertainty trajectory (first 5): {unc_traj[:5]}")
            print(f"  Uncertainty trajectory (last 5): {unc_traj[-5:]}")
            print(f"  Total events for this lineage: {len(evs)}")

            # Promotion check
            lessons = kr.list_principles() # Let's fetch principles to see if this lineage promoted
            promoted_p = [p for p in lessons if lineage_id in (p.associated_lineage_ids or [])]
            if promoted_p:
                for p in promoted_p:
                    print(f"  Promoted to Principle: id={p.id}, status={p.status}, created_at_step={p.created_at_step}")

        # Part 2: Confidence Dynamics
        all_confs = [e.confidence_after for e in events]
        if all_confs:
            print("\n=== PART 2: CONFIDENCE DYNAMICS ===")
            print(f"Min Confidence: {np.min(all_confs):.4f}")
            print(f"Max Confidence: {np.max(all_confs):.4f}")
            print(f"Median Confidence: {np.median(all_confs):.4f}")
            print(f"Mean Confidence: {np.mean(all_confs):.4f}")
            print(f"Std Dev Confidence: {np.std(all_confs):.4f}")

        # Part 3: Uncertainty Dynamics
        all_uncs = [e.uncertainty_after for e in events]
        if all_uncs:
            print("\n=== PART 3: UNCERTAINTY DYNAMICS ===")
            print(f"Min Uncertainty: {np.min(all_uncs):.4f}")
            print(f"Max Uncertainty: {np.max(all_uncs):.4f}")
            print(f"Median Uncertainty: {np.median(all_uncs):.4f}")
            print(f"Mean Uncertainty: {np.mean(all_uncs):.4f}")
            print(f"Std Dev Uncertainty: {np.std(all_uncs):.4f}")

        # Part 4: Evidence Weight Analysis
        weights = [e.evidence_weight for e in events if e.evidence_weight is not None]
        if weights:
            print("\n=== PART 4: EVIDENCE WEIGHT ANALYSIS ===")
            print(f"Total weights: {len(weights)}")
            print(f"Min Weight: {np.min(weights):.4f}")
            print(f"Max Weight: {np.max(weights):.4f}")
            print(f"Median Weight: {np.median(weights):.4f}")
            print(f"Mean Weight: {np.mean(weights):.4f}")
            print(f"Std Dev Weight: {np.std(weights):.4f}")

            # Histogram simulation
            hist, bin_edges = np.histogram(weights, bins=5)
            print("Histogram bins:")
            for i in range(len(hist)):
                print(f"  Bin {bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}: {hist[i]} events")

    # Part 5: Promotion behavior
    lessons_list = kr.list_principles()
    print("\n=== PART 5: PROMOTIONS ===")
    print(f"Total Principles/Candidates in KR: {len(lessons_list)}")
    for p in lessons_list:
        print(f"Principle: {p.statement[:60]}... | Status: {p.status} | Created step: {p.created_at_step} | Support count: {p.support_count}")

    # Part 7: World Model Transitions
    wms = kr.list_world_models()
    print("\n=== PART 7: WORLD MODEL TRANSITIONS ===")
    print(f"Total World Model Snapshots: {len(wms)}")
    if wms:
        latest_wm = wms[-1]
        print(f"Latest WM step: {latest_wm.step}")
        print(f"Latest WM regime_constraints: {latest_wm.regime_constraints}")
        print(f"Latest WM active_principle_ids count: {len(latest_wm.active_principle_ids)}")

if __name__ == "__main__":
    analyze_learning_dynamics()
