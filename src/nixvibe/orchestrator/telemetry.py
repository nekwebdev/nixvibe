"""Run telemetry contract helpers."""

from __future__ import annotations


def build_run_telemetry(
    *,
    route: str,
    mode: str,
    specialist_count: int,
    generated_file_count: int,
    proposed_file_count: int,
    written_file_count: int,
    pre_write_validation_executed: bool,
    post_write_validation_executed: bool,
    specialist_execution_ms: int,
    artifact_materialization_ms: int,
    validation_pre_write_ms: int,
    validation_post_write_ms: int,
    ledger_inspection_ms: int,
    total_duration_ms: int,
) -> dict[str, object]:
    normalized_specialist_count = max(0, int(specialist_count))
    normalized_generated_file_count = max(0, int(generated_file_count))
    normalized_proposed_file_count = max(0, int(proposed_file_count))
    normalized_written_file_count = max(0, int(written_file_count))

    normalized_specialist_execution_ms = _normalize_ms(specialist_execution_ms)
    normalized_materialization_ms = _normalize_ms(artifact_materialization_ms)
    normalized_validation_pre_write_ms = _normalize_ms(validation_pre_write_ms)
    normalized_validation_post_write_ms = _normalize_ms(validation_post_write_ms)
    normalized_ledger_inspection_ms = _normalize_ms(ledger_inspection_ms)
    normalized_total_duration_ms = _normalize_ms(total_duration_ms)

    validation_checkpoint_count = int(bool(pre_write_validation_executed)) + int(
        bool(post_write_validation_executed)
    )
    validation_total_ms = normalized_validation_pre_write_ms + normalized_validation_post_write_ms
    specialist_average_ms = (
        int(round(normalized_specialist_execution_ms / normalized_specialist_count))
        if normalized_specialist_count > 0
        else 0
    )

    return {
        "contract": "run-telemetry/v1",
        "route": route,
        "mode": mode,
        "specialist_count": normalized_specialist_count,
        "generated_file_count": normalized_generated_file_count,
        "proposed_file_count": normalized_proposed_file_count,
        "written_file_count": normalized_written_file_count,
        "validation_checkpoint_count": validation_checkpoint_count,
        "total_duration_ms": normalized_total_duration_ms,
        "specialist_execution_ms": normalized_specialist_execution_ms,
        "specialist_average_ms": specialist_average_ms,
        "artifact_materialization_ms": normalized_materialization_ms,
        "validation_pre_write_ms": normalized_validation_pre_write_ms,
        "validation_post_write_ms": normalized_validation_post_write_ms,
        "validation_total_ms": validation_total_ms,
        "ledger_inspection_ms": normalized_ledger_inspection_ms,
        "summary": _summary(
            total_duration_ms=normalized_total_duration_ms,
            specialist_count=normalized_specialist_count,
            validation_checkpoint_count=validation_checkpoint_count,
        ),
    }


def _normalize_ms(value: int | float) -> int:
    return max(0, int(value))


def _summary(
    *,
    total_duration_ms: int,
    specialist_count: int,
    validation_checkpoint_count: int,
) -> str:
    return (
        f"Run completed in {total_duration_ms} ms with "
        f"{specialist_count} specialist(s) and "
        f"{validation_checkpoint_count} validation checkpoint(s)."
    )
