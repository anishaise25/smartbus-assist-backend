"""Builds the spoken sentences (any language) for every response."""
from i18n import tr, plural


def journey(net, j, lang):
    parts = []
    for i, leg in enumerate(j["legs"]):
        frm = net.name(leg["board_stop_id"], lang)
        to = net.name(leg["get_off_stop_id"], lang)
        parts.append(tr(lang, "take_first" if i == 0 else "take_next", bus=leg["bus_number"], frm=frm))
        parts.append(tr(lang, "get_off", to=to, stops=plural(lang, "stops", leg["num_stops"])))
    parts.append(tr(lang, "total_time", m=j["total_minutes"]))
    return " ".join(parts)


def search_summary(net, res, lang):
    frm, to = net.name(res["from"]["id"], lang), net.name(res["to"]["id"], lang)
    for j in res["direct_buses"] + res["transfer_routes"]:
        j["speech"] = journey(net, j, lang)
    if not res["found"]:
        return tr(lang, "not_found", frm=frm, to=to)
    best = res["best"]
    n = len(res["direct_buses"]) + len(res["transfer_routes"])
    if best["transfers"] == 0:
        lead = tr(lang, "direct_lead", bus=best["buses"][0], frm=frm, to=to)
    else:
        lead = tr(lang, "change_lead", changes=plural(lang, "changes", best["transfers"]))
    return f"{lead} {best['speech']} {plural(lang, 'options', n)}"


def identify(net, bus, conf, lang, dest_id=None, status=None, alt=None):
    a, b = net.name(bus["route"][0], lang), net.name(bus["route"][-1], lang)
    say = tr(lang, "ident", bus=bus["number"], a=a, b=b)
    if conf < 0.8:
        say += tr(lang, "low_conf")
    if dest_id is not None and status:
        dest = net.name(dest_id, lang)
        say += tr(lang, {"not_going": "not_go", "board": "goes_board", "opposite": "opposite"}[status], dest=dest)
        if alt:
            say += " " + journey(net, alt, lang)
    return say


def sos(net, near, link, n_contacts, lang):
    if near:
        where = tr(lang, "sos_near", stop=net.name(near["id"], lang))
    else:
        where = tr(lang, "sos_unknown")
    return tr(lang, "sos_text", where=where, link=link), \
        tr(lang, "sos_sent" if n_contacts else "sos_nocontacts")
