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
    }


def split(state, req_id, counter):
    children = []
    remaining = state["remaining"]
    if remaining > 0 and state["bands"]:
        band = state["bands"][0]
        counter.scanned += 1
        take = min(remaining, band["capacity"])
        children.append({"child_id": "c%d" % (len(state["children"]) + 1),
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


def settle(state, req_id, fills, counter):
    filled_total = 0
    for price, qty in fills:
        need = qty
        for child in state["children"]:
            counter.scanned += 1
            if child["price"] != price:
                continue
            already = state["filled"].get(child["child_id"], 0)
            room = child["qty"] - already
            if room <= 0:
                continue
            take = min(room, need)
            state["filled"][child["child_id"]] = already + take
            need -= take
            filled_total += take
            if need == 0:
                break
    state["seen"].append(req_id)
    return {
        "req_id": req_id,
        "status": "ok",
        "filled": filled_total,
        "remaining": state["remaining"],
        "scanned": counter.scanned,
    }
