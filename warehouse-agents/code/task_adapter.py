from __future__ import annotations

from typing import Any

from .base import AssignedTask


def to_sub_agent_task_description(task: AssignedTask, observation: dict[str, Any]) -> dict[str, Any]:
    """Convert a main-agent semantic task into a sub-agent task description."""

    if task.role == "shuttle":
        return _shuttle_task(task)
    if task.role == "pallet_arm":
        return _pallet_arm_task(task)
    if task.role == "transporter":
        return _transporter_task(task)
    return _generic_task(task)


def _shuttle_task(task: AssignedTask) -> dict[str, Any]:
    refs = {
        "shelf_ref": task.params.get("shelf_ref", "shelf_1"),
        "package_group_ref": task.params.get("package_group_ref", "all_available"),
        "conveyor_ref": task.params.get("conveyor_ref", "default_conveyor"),
        "shuttle_ref": task.params.get("shuttle_ref", "default_shuttle"),
    }
    return {
        "task_id": task.task_id,
        "role": task.role,
        "task_type": "pick_shelf_batch_to_conveyor",
        "description": (
            f"Pick {refs['package_group_ref']} packages from {refs['shelf_ref']} as one batch, "
            f"then feed them to {refs['conveyor_ref']} using {refs['shuttle_ref']}."
        ),
        "refs": refs,
        "lookup": {
            "shelf": "obs.static.shelves[refs.shelf_ref]",
            "packages": "obs.dynamic.shelf_inventory[refs.shelf_ref] when package_group_ref is all_available",
            "conveyor": "obs.static.infrastructure[refs.conveyor_ref]",
            "shuttle": "obs.static.infrastructure[refs.shuttle_ref]",
        },
        "expected_command_endpoint": "/shuttle/pick_to_conveyor",
    }


def _pallet_arm_task(task: AssignedTask) -> dict[str, Any]:
    refs = {
        "candidate_group_ref": task.params.get("candidate_group_ref", "available_candidates"),
        "target_grid_ref": task.params.get("target_grid_ref", "default_pallet_grid"),
        "arm_ref": task.params.get("arm_ref", "default_pallet_arm"),
        "pallet_ref": task.params.get("pallet_ref", "default_pallet"),
    }
    return {
        "task_id": task.task_id,
        "role": task.role,
        "task_type": "palletize_candidates_to_grid",
        "description": (
            f"Move available conveyor candidates from {refs['candidate_group_ref']} onto "
            f"{refs['target_grid_ref']} using {refs['arm_ref']}."
        ),
        "refs": refs,
        "lookup": {
            "candidate_pool": "obs.dynamic.candidate_pool",
            "target_grid": "obs.static.fixed_positions.pallet_grid_targets",
            "arm": "obs.static.infrastructure[refs.arm_ref]",
            "pallet": "obs.static.infrastructure (default_pallet_index field)",
        },
        "expected_command_endpoint": "/arm/pick_place",
    }


def _transporter_task(task: AssignedTask) -> dict[str, Any]:
    refs = {
        "pallet_ref": task.params.get("pallet_ref", "default_pallet"),
        "outbound_ref": task.params.get("outbound_ref", "outbound_target"),
        "transporter_ref": task.params.get("transporter_ref", "default_transporter"),
    }
    return {
        "task_id": task.task_id,
        "role": task.role,
        "task_type": "move_loaded_pallet_to_target",
        "description": (
            f"Move {refs['pallet_ref']} to {refs['outbound_ref']} using "
            f"{refs['transporter_ref']}."
        ),
        "refs": refs,
        "lookup": {
            "pallet": "obs.static.infrastructure (default_pallet_index field)",
            "target": "obs.static.fixed_positions.outbound_target",
            "transporter": "obs.static.infrastructure[refs.transporter_ref]",
        },
        "expected_command_endpoint": "/transporter/move_pallet",
    }


def _generic_task(task: AssignedTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "role": task.role,
        "task_type": "generic",
        "description": task.goal,
        "refs": dict(task.params),
        "lookup": {},
        "expected_command_endpoint": "",
    }
