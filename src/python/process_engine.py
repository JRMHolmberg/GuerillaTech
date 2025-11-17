from datetime import datetime
from typing import Dict, Any, Tuple

from .core_models import ProcessModel, Checkpoint, Metric, ActionCard, ActionCardCluster, OrgFunction


class CoreEvaluator:
    """
    Interface för att utvärdera en ProcessModel.
    Den riktiga logiken (t.ex. koherens) implementeras i privata projekt.
    """
    def evaluate(self, process: ProcessModel) -> Dict[str, Any]:
        raise NotImplementedError


class ProcessEngine:
    def __init__(self, evaluator: CoreEvaluator):
        self.evaluator = evaluator

    # --- ProcessPlan-validering --- #

    def can_start_process(self, process: ProcessModel) -> bool:
        plan = process.plan
        if not plan:
            return False
        if not plan.purpose or not plan.goals:
            return False
        if not plan.owner_id:
            return False
        if not plan.checkpoint_ids:
            return False
        if not plan.documents or len(plan.documents) == 0:
            return False
        if not plan.validated:
            return False
        return True

    # --- Starta process --- #

    def start_process(self, process: ProcessModel, now: str | None = None) -> Tuple[ProcessModel, Dict[str, Any]]:
        if process.status != "NOT_STARTED":
            raise ValueError("Process not in NOT_STARTED state.")
        if not self.can_start_process(process):
            raise ValueError("Process plan incomplete or not validated.")

        now = now or datetime.utcnow().isoformat()
        process.status = "UNDER_WORK"

        event = {
            "event_type": "PROCESS_STARTED",
            "process_id": process.id,
            "node_id": process.metadata.get("node_id") if process.metadata else None,
            "owner": process.owner_id,
            "supervisor": process.supervisor_id,
            "timestamp": now,
        }
        return process, event

    # --- Klarmarkera delmål (checkpoint) --- #

    def mark_checkpoint_done(self, process: ProcessModel, checkpoint_id: str, user_id: str,
                             now: str | None = None) -> Tuple[ProcessModel, Checkpoint]:
        now = now or datetime.utcnow().isoformat()
        cp = self._find_checkpoint(process, checkpoint_id)

        cp.status = "DONE"
        cp.completed_at = now
        cp.completed_by = user_id

        if cp.metrics is None:
            cp.metrics = []

        auto_metrics = self._generate_auto_metrics(process, cp)
        cp.metrics.extend(auto_metrics)

        # uppdatera processens övergripande bedömning
        evaluation = self.evaluator.evaluate(process)
        process.metadata = process.metadata or {}
        process.metadata["last_evaluation"] = evaluation

        return process, cp

    def _find_checkpoint(self, process: ProcessModel, checkpoint_id: str) -> Checkpoint:
        for cp in process.checkpoints:
            if cp.id == checkpoint_id:
                return cp
        raise ValueError(f"Checkpoint {checkpoint_id} not found.")

    def _generate_auto_metrics(self, process: ProcessModel, cp: Checkpoint) -> list[Metric]:
        metrics: list[Metric] = []

        # Placeholder – här lägger man egen logik i privata projekt.
        metrics.append(Metric(
            id="METRIC-DURATION",
            name="Time to complete checkpoint",
            value=None,
            unit="days"
        ))
        metrics.append(Metric(
            id="METRIC-ITERATIONS",
            name="Number of feedback cycles",
            value=None,
            unit="count"
        ))
        metrics.append(Metric(
            id="METRIC-REWORK_FLAG",
            name="Rework required",
            value=None,
            unit="bool"
        ))
        metrics.append(Metric(
            id="METRIC-COHERENCE_BEFORE",
            name="Coherence before completion",
            value=None
        ))
        metrics.append(Metric(
            id="METRIC-COHERENCE_AFTER",
            name="Coherence after completion",
            value=None
        ))

        return metrics
