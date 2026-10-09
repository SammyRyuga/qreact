"""
LocalRepairPlanner: generates candidate repairs (bounded to the given
RepairRegion only -- it never invokes a full re-transpilation to produce a
supposedly "local" candidate) and scores them with a deterministic,
explainable weighted formula.

Scoring determines TRY ORDER ONLY. It never substitutes for verification:
a high-scoring candidate that fails RepairVerifier is rejected outright,
full stop -- see tests/test_repair.py for an adversarial case asserting
exactly this.
"""
from __future__ import annotations
from dataclasses import dataclass

from .candidates import (
    PURE_RELABEL, LOCAL_SWAP, ALT_MAPPING,
    generate_relabel_candidate, generate_swap_candidate,
)


@dataclass(frozen=True)
class ScoringWeights:
    lambda_cost: float = 0.02
    lambda_depth: float = 0.1
    lambda_swaps: float = 0.3
    lambda_changes: float = 0.05
    lambda_region: float = 1.0


class LocalRepairPlanner:
    def __init__(self, weights: ScoringWeights | None = None, max_candidates: int = 3,
                 max_swap_chain_length: int = 2):
        self.weights = weights or ScoringWeights()
        self.max_candidates = max_candidates
        self.max_swap_chain_length = max_swap_chain_length

    def generate_candidates(self, artifact, drift_event, region, calib_snapshot) -> list:
        if region.too_large:
            return []
        candidates = []

        c = generate_relabel_candidate(artifact, drift_event, region, calib_snapshot, candidate_type=PURE_RELABEL)
        if c is not None:
            candidates.append(c)

        c = generate_swap_candidate(artifact, drift_event, region, calib_snapshot,
                                     max_chain_length=self.max_swap_chain_length)
        if c is not None:
            candidates.append(c)

        c = generate_relabel_candidate(artifact, drift_event, region, calib_snapshot,
                                        candidate_type=ALT_MAPPING, prefer_far=True)
        if c is not None and not _duplicates_existing(c, candidates):
            candidates.append(c)

        candidates = candidates[: self.max_candidates]
        for c in candidates:
            c.disruption_score = self.score(c, region)
        candidates.sort(key=lambda c: c.disruption_score, reverse=True)
        return candidates

    def score(self, candidate, region) -> float:
        """
        score = health_improvement
                - lambda_cost    * repair_cost
                - lambda_depth   * depth_increase
                - lambda_swaps   * added_swaps
                - lambda_changes * changed_operations
                - lambda_region  * region_fraction

        health_improvement is a fixed constant (1.0): every candidate
        reaching this point already moves the drifted resource off of
        itself by construction, so this term does not need its own free
        parameter to be meaningful -- the weighted penalty terms are what
        differentiate candidates from each other. Every component is
        exposed on the candidate for inspection; nothing here is hidden
        inside an opaque model.
        """
        w = self.weights
        return float(
            1.0
            - w.lambda_cost * candidate.estimated_cost
            - w.lambda_depth * candidate.estimated_depth_delta
            - w.lambda_swaps * len(candidate.inserted_swaps)
            - w.lambda_changes * len(candidate.changed_operation_ids)
            - w.lambda_region * region.region_fraction
        )


def _duplicates_existing(candidate, existing) -> bool:
    return any(e.new_layout == candidate.new_layout for e in existing)
