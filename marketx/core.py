"""拆单与结算核心。"""


class Counter:
    """记录本轮检查过的子单条数。"""

    def __init__(self):
        self.scanned = 0


def new_state(order_id, side, qty, max_child, bands):
    ordered = sorted(bands, key=lambda band: band[0], reverse=(side == "sell"))
    return {
        "order": {"order_id": order_id, "side": side, "qty": qty},
        "max_child": max_child,
        "bands": [{"price": price, "capacity": cap} for price, cap in ordered],
        "children": [],
        "filled": {},
        "remaining": qty,
        "seen": {},
    }


def split(state, req_id, counter):
    if req_id in state["seen"]:
        return {
            "req_id": req_id,
            "status": "replay",
            "children": [],
            "remaining": state["remaining"],
            "scanned": counter.scanned,
        }
    state["seen"][req_id] = True
    allocated = {}
    for child in state["children"]:
        allocated[child["price"]] = allocated.get(child["price"], 0) + child["qty"]
    children = []
    remaining = state["remaining"]
    if remaining > 0:
        for band in state["bands"]:
            if remaining <= 0:
                break
            counter.scanned += 1
            room = band["capacity"] - allocated.get(band["price"], 0)
            take = min(remaining, state["max_child"], room)
            if take <= 0:
                continue
            children.append({"child_id": "c%d" % (len(state["children"]) + len(children) + 1),
                             "price": band["price"], "qty": take})
            allocated[band["price"]] = allocated.get(band["price"], 0) + take
            remaining -= take
    state["children"].extend(children)
    state["remaining"] = remaining
    return {
        "req_id": req_id,
        "status": "ok",
        "children": [[c["price"], c["qty"]] for c in children],
        "remaining": state["remaining"],
        "scanned": counter.scanned,
    }


def _child_index(state):
    children = state["children"]
    index = state.get("index")
    if index is None or index.get("n") != len(children):
        by_price = {}
        for pos, child in enumerate(children):
            by_price.setdefault(str(child["price"]), []).append(pos)
        index = {"n": len(children), "by_price": by_price, "cursor": {}}
        state["index"] = index
    return index


def settle(state, req_id, fills, counter):
    if req_id in state["seen"]:
        return {
            "req_id": req_id,
            "status": "replay",
            "filled": 0,
            "remaining": state["remaining"],
            "scanned": counter.scanned,
        }
    state["seen"][req_id] = True
    index = _child_index(state)
    by_price = index["by_price"]
    cursors = index["cursor"]
    filled_total = 0
    for price, qty in fills:
        need = qty
        positions = by_price.get(str(price), [])
        cursor = cursors.get(str(price), 0)
        while need > 0 and cursor < len(positions):
            child = state["children"][positions[cursor]]
            counter.scanned += 1
            already = state["filled"].get(child["child_id"], 0)
            room = child["qty"] - already
            if room <= 0:
                cursor += 1
                continue
            take = min(room, need)
            state["filled"][child["child_id"]] = already + take
            need -= take
            filled_total += take
            if take == room:
                cursor += 1
        cursors[str(price)] = cursor
        if need > 0:
            state["remaining"] += need
    return {
        "req_id": req_id,
        "status": "ok",
        "filled": filled_total,
        "remaining": state["remaining"],
        "scanned": counter.scanned,
    }
