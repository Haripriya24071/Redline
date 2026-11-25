"""E8: Deadlock detection (Resource Allocation Graph) and prevention (resource ordering)."""

from __future__ import annotations

from typing import Any

# Fixed resource acquisition order to prevent circular wait (Coffman condition 4)
RESOURCE_ORDER: dict[str, int] = {
    "ICU": 1,
    "EMERGENCY": 2,
    "VENTILATOR": 3,
    "NEURO": 4,
    "SPECIALIST": 5,
}


def sort_facilities_for_acquisition(facilities: list[str]) -> list[str]:
    """Enforce global resource ordering to prevent circular wait."""
    return sorted(facilities, key=lambda f: RESOURCE_ORDER.get(f, 99))


class ResourceAllocationGraph:
    """Directed bipartite graph between request processes and single-unit resources."""

    def __init__(self) -> None:
        # resource_id -> holding request_id
        self.held_by: dict[str, str] = {}
        # request_id -> set of requested resource_ids
        self.waiting_for: dict[str, list[str]] = {}
        # request_id -> priority (1 = highest)
        self.priorities: dict[str, int] = {}

    def register_request(self, req_id: str, priority: int) -> None:
        self.priorities[req_id] = priority
        self.waiting_for.setdefault(req_id, [])

    def add_hold(self, req_id: str, resource_id: str, priority: int = 5) -> None:
        self.priorities.setdefault(req_id, priority)
        self.held_by[resource_id] = req_id
        if req_id in self.waiting_for and resource_id in self.waiting_for[req_id]:
            self.waiting_for[req_id].remove(resource_id)

    def add_wait(self, req_id: str, resource_id: str, priority: int = 5) -> None:
        self.priorities.setdefault(req_id, priority)
        self.waiting_for.setdefault(req_id, [])
        if resource_id not in self.waiting_for[req_id]:
            self.waiting_for[req_id].append(resource_id)

    def release_request(self, req_id: str) -> list[str]:
        """Release all holds and waits for a victim or completed request."""
        released = [res for res, holder in self.held_by.items() if holder == req_id]
        for res in released:
            del self.held_by[res]
        self.waiting_for.pop(req_id, None)
        return released

    def detect_cycle(self) -> list[str] | None:
        """Detect a cycle in the RAG (returns cycle path or None)."""
        # Build wait-for adjacency: req_a -> req_b if req_a waits for resource held by req_b
        adj: dict[str, list[tuple[str, str]]] = {}
        for req_id, res_list in self.waiting_for.items():
            for res_id in res_list:
                holder = self.held_by.get(res_id)
                if holder and holder != req_id:
                    adj.setdefault(req_id, []).append((res_id, holder))

        visited: set[str] = set()
        stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> list[str] | None:
            visited.add(node)
            stack.add(node)
            for res_id, nxt in adj.get(node, []):
                if nxt not in visited:
                    path.extend([node, res_id])
                    res = dfs(nxt)
                    if res:
                        return res
                    path.pop()
                    path.pop()
                elif nxt in stack:
                    cycle_start = len(path)
                    for idx, item in enumerate(path):
                        if item == nxt:
                            cycle_start = idx
                            break
                    return path[cycle_start:] + [node, res_id, nxt]
            stack.remove(node)
            return None

        for req_id in list(adj.keys()):
            if req_id not in visited:
                path.clear()
                found = dfs(req_id)
                if found:
                    return found
        return None

    def recover_if_deadlocked(self) -> dict[str, Any]:
        """If a cycle exists, pick the lowest-priority request as victim and release its holds."""
        cycle = self.detect_cycle()
        if not cycle:
            return {"deadlocked": False, "cycle": None, "victim": None, "released": []}

        # Identify process nodes in the cycle (every even index in alternating req/res path)
        cycle_reqs = [node for node in cycle if node in self.priorities]
        victim = max(cycle_reqs, key=lambda r: self.priorities.get(r, 5))
        released = self.release_request(victim)
        return {
            "deadlocked": True,
            "cycle": cycle,
            "victim": victim,
            "released": released,
        }

    def snapshot(self) -> dict[str, Any]:
        cycle = self.detect_cycle()
        edges = []
        for res_id, holder in self.held_by.items():
            edges.append({"from": holder, "to": res_id, "type": "holds"})
        for req_id, res_list in self.waiting_for.items():
            for res_id in res_list:
                edges.append({"from": req_id, "to": res_id, "type": "requests"})
        return {
            "deadlocked": cycle is not None,
            "cycle": cycle,
            "edges": edges,
            "held_by": dict(self.held_by),
            "waiting_for": dict(self.waiting_for),
        }

