"""拆单与结算核心。"""


class Counter:
    """记录本轮检查过的子单条数。"""

    def __init__(self):
        self.scanned = 0


def new_state(order_id, side, qty, max_child, bands):
    return {
        "order": {"order_id": order_id, "side": side, "qty": qty},
        "max_child": max_child,
        "bands": [{"price": price, "capacity": cap} for price, cap in bands],
        "children": [],
        "filled": {},
        "remaining": qty,
        "seen": [],
        "pending": {},
        "pending_head": {},
        "indexed": 0,
    }


def _band_order(state):
    reverse = state["order"]["side"] == "sell"
    return sorted(state["bands"], key=lambda band: band["price"], reverse=reverse)


def split(state, req_id, counter):
    if req_id in state["seen"]:
        return {
            "req_id": req_id,
            "status": "replay",
            "children": [],
            "remaining": state["remaining"],
            "scanned": counter.scanned,
        }
    allocated = {}
    for child in state["children"]:
        counter.scanned += 1
        allocated[child["price"]] = allocated.get(child["price"], 0) + child["qty"]
    children = []
    remaining = state["remaining"]
    for band in _band_order(state):
        if remaining <= 0:
            break
        room = band["capacity"] - allocated.get(band["price"], 0)
        take = min(remaining, room, state["max_child"])
        if take <= 0:
            continue
        children.append({"child_id": "c%d" % (len(state["children"]) + len(children) + 1),
                         "price": band["price"], "qty": take})
        remaining -= take
    state["children"].extend(children)
    state["remaining"] = remaining
    state["seen"].append(req_id)
    return {
        "req_id": req_id,
        "status": "ok",
        "children": [[c["price"], c["qty"]] for c in children],
        "remaining": state["remaining"],
        "scanned": counter.scanned,
    }


def _ensure_index(state, counter):
    children = state["children"]
    pending = state.setdefault("pending", {})
    start = state.get("indexed", 0)
    for pos in range(start, len(children)):
        child = children[pos]
        counter.scanned += 1
        already = state["filled"].get(child["child_id"], 0)
        if child["qty"] - already > 0:
            pending.setdefault(str(child["price"]), []).append(pos)
    state["indexed"] = len(children)


def settle(state, req_id, fills, counter):
    if req_id in state["seen"]:
        return {
            "req_id": req_id,
            "status": "replay",
            "filled": 0,
            "remaining": state["remaining"],
            "scanned": counter.scanned,
        }
    _ensure_index(state, counter)
    pending = state["pending"]
    heads = state.setdefault("pending_head", {})
    filled_total = 0
    for price, qty in fills:
        key = str(price)
        ids = pending.get(key, [])
        head = heads.get(key, 0)
        need = qty
        while need > 0 and head < len(ids):
            child = state["children"][ids[head]]
            counter.scanned += 1
            already = state["filled"].get(child["child_id"], 0)
            room = child["qty"] - already
            if room <= 0:
                head += 1
                continue
            take = min(room, need)
            state["filled"][child["child_id"]] = already + take
            need -= take
            filled_total += take
            if already + take >= child["qty"]:
                head += 1
        heads[key] = head
        if need > 0:
            state["remaining"] += need
    state["seen"].append(req_id)
    return {
        "req_id": req_id,
        "status": "ok",
        "filled": filled_total,
        "remaining": state["remaining"],
        "scanned": counter.scanned,
    }
