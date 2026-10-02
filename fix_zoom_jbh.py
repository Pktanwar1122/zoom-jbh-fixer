
"""
Auto-enables "Allow participants to join anytime" on every upcoming Zoom meeting
created by Momence under Prateek's account. Safe to run repeatedly.
 
Env vars required:
  ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET  (Server-to-Server OAuth app)
  ZOOM_USER_EMAIL  (Prateek's Zoom login email)
Optional:
  LOOKAHEAD_HOURS  (default 72) - only touch meetings starting within this window
"""
import os, re, sys, base64, datetime as dt
import requests
 
API = "https://api.zoom.us/v2"
ACC, CID, SEC = os.environ["ZOOM_ACCOUNT_ID"], os.environ["ZOOM_CLIENT_ID"], os.environ["ZOOM_CLIENT_SECRET"]
USER = os.environ["ZOOM_USER_EMAIL"]
LOOKAHEAD = int(os.environ.get("LOOKAHEAD_HOURS", "72"))
# Optional regex the Momence meeting topic must match, e.g. "Yoga|Session" (case-insensitive)
TOPIC_RE = re.compile(os.environ["MATCH_TOPIC"], re.I) if os.environ.get("MATCH_TOPIC") else None
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
 
DESIRED = {"join_before_host": True, "jbh_time": 0, "waiting_room": False}
 
 
def token():
    auth = base64.b64encode(f"{CID}:{SEC}".encode()).decode()
    r = requests.post(
        "https://zoom.us/oauth/token",
        params={"grant_type": "account_credentials", "account_id": ACC},
        headers={"Authorization": f"Basic {auth}"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]
 
 
def upcoming(s):
    params, out = {"type": "upcoming", "page_size": 300}, []
    while True:
        r = s.get(f"{API}/users/{USER}/meetings", params=params, timeout=30)
        r.raise_for_status()
        d = r.json()
        out += d.get("meetings", [])
        if not d.get("next_page_token"):
            return out
        params["next_page_token"] = d["next_page_token"]
 
 
def mask(mid):
    # Public repo => public logs. Never print full meeting IDs or topics.
    return "***" + str(mid)[-4:]
 
 
def main():
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token()}"
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now + dt.timedelta(hours=LOOKAHEAD)
    fixed = checked = 0
 
    for m in upcoming(s):
        st = m.get("start_time")
        if st:
            start = dt.datetime.fromisoformat(st.replace("Z", "+00:00"))
            if start > cutoff or start < now - dt.timedelta(hours=2):
                continue
        checked += 1
        r = s.get(f"{API}/meetings/{m['id']}", timeout=30)
        if r.status_code != 200:
            print(f"skip {mask(m['id'])}: HTTP {r.status_code}")
            continue
        meeting = r.json()
        src = meeting.get("creation_source", "unknown")
        topic = meeting.get("topic", "")
        # Only Momence meetings: if MATCH_TOPIC is set, match on topic alone;
        # otherwise fall back to "created via API" (not Zoom app/web)
        is_momence = bool(TOPIC_RE.search(topic)) if TOPIC_RE else src == "open_api"
        if not is_momence:
            print(f"ignore {mask(m['id'])}  source={src}")
            continue
        cur = meeting.get("settings", {})
        if all(cur.get(k) == v for k, v in DESIRED.items()):
            continue
        if DRY_RUN:
            print(f"WOULD FIX {mask(m['id'])}  {st}")
            continue
        p = s.patch(f"{API}/meetings/{m['id']}", json={"settings": DESIRED}, timeout=30)
        if p.status_code == 204:
            fixed += 1
            print(f"fixed {mask(m['id'])}  {st}")
        else:
            print(f"FAILED {mask(m['id'])}: HTTP {p.status_code}")
 
    print(f"done: checked {checked}, fixed {fixed}")
 
 
if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print("HTTP error:", e.response.status_code, "on", e.request.method); sys.exit(1)
 
