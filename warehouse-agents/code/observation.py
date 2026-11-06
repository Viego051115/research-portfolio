from __future__ import annotations

from typing import Any

# ---- 硬编码 fallback（dry-run / 无场景数据时使用）----
PALLET_GRID_OFFSETS = [[-0.35, -0.25], [0.25, -0.25], [-0.35, 0.25], [0.25, 0.25]]
PALLET_GRID_TARGETS = [[20.9, 7.7, 0.28], [21.8, 7.7, 0.28], [21.35, 8.3, 0.28]]
OUTBOUND_TARGET = [24.0, 12.0, 0.0]


def build_observation_slices(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """把原始 API 状态切成每个角色专属的观测视图。

    static/dynamic 分层 + 场景数据动态坐标（优先场景，fallback 硬编码）。
    """

    state = raw.get("state", {})
    shelf_packages = raw.get("shelf_packages", {})
    scene = state.get("scene", {})
    agents = state.get("agents", state.get("agent_positions", {}))

    # ---- 从原始数据提取货架信息 ----
    scene_shelves = {
        int(item["index"]): item
        for item in scene.get("shelves", [])
        if item.get("index") is not None
    }
    shelves = {}
    for index, shelf in shelf_packages.items():
        index = int(index)
        ss = scene_shelves.get(index, {})
        ref = f"shelf_{index}"
        packages = [item.get("name") for item in shelf.get("packages", []) if item.get("name")]
        shelves[ref] = {
            "shelf_index": index,
            "shelf_name": shelf.get("shelf_name", ss.get("name", f"Shelf_{index}")),
            "available_package_names": packages,
        }

    # ---- 从场景实时读取（优先） + 硬编码 fallback ----
    conveyors = _conveyor_names(scene.get("conveyors", {}), state.get("conveyors", ["DemoConveyor"]))
    pallets_data = _pallet_data(scene.get("pallets", []), state.get("pallets", ["Pallet_1"]))
    transport_targets = list(scene.get("transport_targets", []))

    # ---- 动态读取 agent 名称（优先 API，fallback 硬编码）----
    _shuttles_list = agents.get("shuttles") or []
    _shuttle_names = [s.get("name", f"shuttle{i+1}") for i, s in enumerate(_shuttles_list)] or ["shuttle1"]
    _first_shuttle = _shuttle_names[0]
    _first_arm = (agents.get("pallet_arms") or agents.get("manipulators") or [{}])[0].get("name", "pallet_arm1")
    _first_transporter = (agents.get("transporters") or [{}])[0].get("name", "transporter1")

    # ---- 构建多区码垛单元（palletizing cells）----
    # 每个 pallet 对应一个 cell，含机械臂、托盘坐标、出库点
    pallet_arms_list = agents.get("pallet_arms") or agents.get("manipulators") or []
    palletizing_cells: list[dict[str, Any]] = []
    for i, pallet in enumerate(pallets_data):
        arm_name = pallet_arms_list[i].get("name", f"pallet_arm{i+1}") if i < len(pallet_arms_list) else f"pallet_arm{i+1}"
        cell_targets = _pallet_grid_targets([pallet], state.get("candidate_pool", [])) or list(PALLET_GRID_TARGETS)
        cell_outbound = _first_position(transport_targets[i:i+1]) or _first_position(transport_targets) or list(OUTBOUND_TARGET)
        palletizing_cells.append({
            "name": pallet.get("name", f"Pallet_{i+1}"),
            "arm": arm_name,
            "pallet_name": pallet.get("name", f"Pallet_{i+1}"),
            "pallet_index": i + 1,
            "dimensions": pallet.get("dimensions"),
            "position": pallet.get("position"),
            "targets": cell_targets,
            "target_count": len(cell_targets),
            "outbound_target": cell_outbound,
        })

    # 兼容旧版单区 fallback
    first_cell = palletizing_cells[0] if palletizing_cells else {}
    outbound_target = first_cell.get("outbound_target", list(OUTBOUND_TARGET))
    pallet_grid_targets = first_cell.get("targets", list(PALLET_GRID_TARGETS))
    total_target_count = sum(c["target_count"] for c in palletizing_cells)

    # ---- 共享基础设施（static）----
    shared_static = {
        "shelves": {
            ref: {"index": data["shelf_index"], "name": data["shelf_name"]}
            for ref, data in shelves.items()
        },
        "infrastructure": {
            "available_conveyors": conveyors,
            "default_conveyor": conveyors[0] if conveyors else "DemoConveyor",
            "default_shuttle": _first_shuttle,
            "default_pallet_arm": _first_arm,
            "default_pallet_index": 1,
            "default_pallet_name": pallets_data[0]["name"] if pallets_data else "Pallet_1",
            "default_transporter": _first_transporter,
        },
    }

    # ================================================================
    #  main 视图
    # ================================================================
    main_obs = {
        "static": {
            "available_roles": ["shuttle", "pallet_arm", "transporter"],
            "shelf_refs": list(shelves.keys()),
            "available_shuttles": _shuttle_names,
        },
        "dynamic": {
            "system_status": "ready",
            "shelf_inventory": {
                ref: len(data["available_package_names"])
                for ref, data in shelves.items()
            },
            "equipment_status": {
                "default_conveyor": "available",
                "default_shuttle": "available",
                "default_pallet_arm": "available",
                "default_pallet": "available",
                "default_transporter": "available",
                "default_pallet_grid": "available",
                "outbound_target": "available",
            },
        },
    }

    # ================================================================
    #  shuttle 视图
    # ================================================================
    shuttle_obs = {
        "static": {
            "shelves": shared_static["shelves"],
            "available_shuttles": _shuttle_names,
            "available_conveyors": conveyors,
            "infrastructure": {
                "default_conveyor": shared_static["infrastructure"]["default_conveyor"],
                "default_shuttle": _first_shuttle,
            },
        },
        "dynamic": {
            "shelf_inventory": {
                ref: data["available_package_names"]
                for ref, data in shelves.items()
            },
        },
    }

    # ================================================================
    #  pallet_arm 视图（多区支持）
    # ================================================================
    pallet_arm_obs = {
        "static": {
            "infrastructure": {
                "default_pallet_arm": _first_arm,
                "default_pallet_index": 1,
                "default_transporter": _first_transporter,
            },
            "palletizing_cells": palletizing_cells,
            "palletizing_policy": (
                "use candidate_index 1 repeatedly — pool advances after each success"
            ),
        },
        "dynamic": {
            "candidate_pool": state.get("candidate_pool", []),
            "candidate_count": len(state.get("candidate_pool", [])),
            "total_target_count": total_target_count,
        },
    }

    # ================================================================
    #  transporter 视图（多出库点支持）
    # ================================================================
    transporter_obs = {
        "static": {
            "infrastructure": {
                "default_pallet_index": 1,
                "default_pallet_name": pallets_data[0]["name"] if pallets_data else "Pallet_1",
                "default_transporter": _first_transporter,
            },
            "outbound_targets": [c["outbound_target"] for c in palletizing_cells],
            "available_pallets": [p["name"] for p in pallets_data if p.get("name")],
        },
    }

    return {
        "raw": raw,
        "main": main_obs,
        "shuttle": shuttle_obs,
        "pallet_arm": pallet_arm_obs,
        "transporter": transporter_obs,
    }


# ════════════════════════════════════════════════════
#  辅助函数（来自新版代码）
# ════════════════════════════════════════════════════

def _conveyor_names(scene_conveyors: Any, legacy_names: Any) -> list[str]:
    if isinstance(scene_conveyors, dict):
        return [item["name"] for item in scene_conveyors.values() if isinstance(item, dict) and item.get("name")]
    if isinstance(scene_conveyors, list):
        items = [item["name"] for item in scene_conveyors if isinstance(item, dict) and item.get("name")]
        if items:
            return items
    return [str(n) for n in legacy_names or []] or ["DemoConveyor"]


def _pallet_data(scene_pallets: Any, legacy_names: Any) -> list[dict[str, Any]]:
    items = [dict(item) for item in (scene_pallets or []) if isinstance(item, dict) and item.get("name")]
    if items:
        return items
    return [{"index": i, "name": str(n)} for i, n in enumerate(legacy_names or [], 1)]


def _first_position(items: list[dict[str, Any]]) -> list[float] | None:
    for item in items:
        pos = item.get("position")
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            vals = list(pos[:3])
            while len(vals) < 3:
                vals.append(0.0)
            return [float(v) for v in vals]
    return None


def _pallet_grid_targets(pallets: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[list[float]]:
    if not pallets:
        return []
    pallet = pallets[0]
    position = _vec3(pallet.get("position"))
    dimensions = _dimensions(pallet.get("dimensions"))
    if position is None or dimensions is None:
        return []

    occupied_offsets = _occupied_pallet_offsets(position, dimensions, candidates)
    free_offsets = [o for o in PALLET_GRID_OFFSETS if tuple(o) not in occupied_offsets]
    targets = []
    available_count = sum(1 for c in (candidates or []) if c.get("status", "candidate") in ("candidate", "on_conveyor"))
    count = max(1, available_count)
    for i, offset in enumerate(free_offsets[:count]):
        pkg = candidates[i] if i < len(candidates or []) else {}
        pkg_dims = _dimensions(pkg.get("dimensions")) or [0.3, 0.3, 0.5]
        target_z = position[2] + dimensions[2] + pkg_dims[2] * 0.5 + 0.015
        targets.append([
            round(position[0] + offset[0], 4),
            round(position[1] + offset[1], 4),
            round(target_z, 4),
        ])
    return targets


def _occupied_pallet_offsets(
    pallet_pos: list[float], pallet_dims: list[float], candidates: list[dict[str, Any]]
) -> set[tuple[float, float]]:
    occupied: set[tuple[float, float]] = set()
    half_l = pallet_dims[0] * 0.5 + 0.1
    half_w = pallet_dims[1] * 0.5 + 0.1
    for item in (candidates or []):
        if item.get("status") not in ("placed", "on_pallet"):
            continue
        pos = _vec3(item.get("position"))
        if pos is None:
            continue
        dx, dy = pos[0] - pallet_pos[0], pos[1] - pallet_pos[1]
        if abs(dx) > half_l or abs(dy) > half_w:
            continue
        closest = min(PALLET_GRID_OFFSETS, key=lambda o: (dx - o[0])**2 + (dy - o[1])**2)
        if (dx - closest[0])**2 + (dy - closest[1])**2 <= 0.04:
            occupied.add(tuple(closest))
    return occupied


def _vec3(value: Any) -> list[float] | None:
    if isinstance(value, dict):
        return [float(value.get("x", 0.0)), float(value.get("y", 0.0)), float(value.get("z", 0.0))]
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        vals = list(value[:3])
        while len(vals) < 3:
            vals.append(0.0)
        return [float(v) for v in vals]
    return None


def _dimensions(value: Any) -> list[float] | None:
    if isinstance(value, dict):
        return [
            float(value.get("length", value.get("x", 0.0))),
            float(value.get("width", value.get("y", 0.0))),
            float(value.get("height", value.get("z", 0.0))),
        ]
    return _vec3(value)
