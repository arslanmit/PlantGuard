"""Lightweight training monitor for PlantGuard training workflows.

This module provides a small compatibility layer used by the production and
improved training entrypoints. It records minimal metadata, emits a JSON report,
and degrades gracefully when optional visualization integrations are absent.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _json_safe(value: Any, visited: set[int] | None = None) -> Any:
    """Convert common training objects into JSON-serializable values."""
    if visited is None:
        visited = set()

    if isinstance(value, (str, int, float, bool, type(None))):
        return value

    value_id = id(value)
    if value_id in visited:
        return "<circular-reference>"

    if is_dataclass(value):
        visited.add(value_id)
        return _json_safe(asdict(value), visited)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        visited.add(value_id)
        return {str(k): _json_safe(v, visited) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        visited.add(value_id)
        return [_json_safe(item, visited) for item in value]
    if hasattr(value, "__dict__"):
        visited.add(value_id)
        return {key: _json_safe(val, visited) for key, val in vars(value).items()}
    return str(value)


class TrainingMonitor:
    """Best-effort monitor used by training scripts and workflows."""

    def __init__(
        self,
        experiment_name: str,
        log_dir: str | Path | None = None,
        auto_launch_tensorboard: bool = False,
        tensorboard_port: int | None = None,
    ) -> None:
        self.experiment_name = experiment_name
        self.auto_launch_tensorboard = auto_launch_tensorboard
        self.tensorboard_port = tensorboard_port
        self.experiment_dir = Path(log_dir) if log_dir is not None else Path("runs") / experiment_name
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.metrics: list[dict[str, Any]] = []
        self.epoch_summaries: list[dict[str, Any]] = []
        self.batch_updates: list[dict[str, Any]] = []
        self._current_epoch: dict[str, Any] | None = None

    def setup_progress_tracking(self, total_epochs: int, steps_per_epoch: int) -> None:
        self.progress_tracking = {"total_epochs": total_epochs, "steps_per_epoch": steps_per_epoch}

    def start_epoch_tracking(self, epoch: int) -> None:
        self._current_epoch = {"epoch": epoch, "started_at": time.time()}

    def update_batch_progress(self, **kwargs: Any) -> None:
        self.batch_updates.append({"timestamp": time.time(), **kwargs})

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None, epoch: int | None = None) -> None:
        self.metrics.append(
            {
                "timestamp": time.time(),
                "step": step,
                "epoch": epoch,
                "metrics": _json_safe(metrics),
            }
        )

    def log_learning_rate(self, optimizer: Any, step: int | None = None) -> None:
        learning_rates = [group.get("lr") for group in getattr(optimizer, "param_groups", [])]
        self.metrics.append(
            {
                "timestamp": time.time(),
                "step": step,
                "metrics": {"learning_rates": learning_rates},
            }
        )

    def log_histograms(self, model: Any, step: int | None = None, log_gradients: bool = False) -> None:
        _ = (model, step, log_gradients)

    def log_confusion_matrix(self, y_true: list[int], y_pred: list[int], class_names: list[str], step: int | None = None) -> None:
        self.metrics.append(
            {
                "timestamp": time.time(),
                "step": step,
                "metrics": {
                    "confusion_matrix": {
                        "num_samples": len(y_true),
                        "class_names": class_names,
                    }
                },
            }
        )

    def log_sample_predictions(
        self,
        sample_images: Any,
        sample_outputs: Any,
        sample_targets: Any,
        class_names: list[str],
        step: int | None = None,
    ) -> None:
        _ = (sample_images, sample_outputs, sample_targets)
        self.metrics.append(
            {
                "timestamp": time.time(),
                "step": step,
                "metrics": {
                    "sample_predictions": {
                        "class_names": class_names,
                    }
                },
            }
        )

    def finish_epoch_tracking(self, val_loss: float, val_accuracy: float, learning_rate: float) -> None:
        epoch_summary = dict(self._current_epoch or {})
        epoch_summary.update(
            {
                "finished_at": time.time(),
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
                "learning_rate": learning_rate,
            }
        )
        self.epoch_summaries.append(epoch_summary)
        self._current_epoch = None

    def save_training_report(self, training_result: Any = None, **sections: Any) -> Path | dict[str, Path]:
        """Persist a JSON training report."""
        report_path = self.experiment_dir / "training_report.json"
        report = {
            "experiment_name": self.experiment_name,
            "generated_at": time.time(),
            "metrics": _json_safe(self.metrics),
            "epoch_summaries": _json_safe(self.epoch_summaries),
            "batch_updates": _json_safe(self.batch_updates[-100:]),
        }
        if training_result is not None:
            report["training_result"] = _json_safe(training_result)
        if sections:
            report["sections"] = _json_safe(sections)

        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

        if sections:
            return {"training_report": report_path}
        return report_path

    def close(self) -> None:
        logger.debug("TrainingMonitor closed for experiment %s", self.experiment_name)
