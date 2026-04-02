"""
Capa de base de datos — SQLite3 puro.
v2: Competiciones múltiples, penales, on-premise.
"""
import sqlite3
import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# On-premise: DB en ./data/ para persistencia entre reinicios
_base = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.environ.get("DATA_DIR", os.path.join(_base, "data"))
os.makedirs(_data_dir, exist_ok=True)
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(_data_dir, "mundial2026.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL, role TEXT DEFAULT 'user',
            is_approved INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            short_name TEXT, season TEXT,
            is_active INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id TEXT, name TEXT NOT NULL, code TEXT,
            flag_url TEXT, group_name TEXT,
            competition_id INTEGER REFERENCES competitions(id)
        );
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id TEXT,
            competition_id INTEGER NOT NULL REFERENCES competitions(id),
            home_team_id INTEGER REFERENCES teams(id),
            away_team_id INTEGER REFERENCES teams(id),
            match_date TEXT NOT NULL, stage TEXT, group_name TEXT, venue TEXT,
            status TEXT DEFAULT 'SCHEDULED',
            home_score INTEGER, away_score INTEGER,
            penalty_home INTEGER, penalty_away INTEGER,
            decided_by_penalties INTEGER DEFAULT 0,
            is_result_final INTEGER DEFAULT 0,
            matchday INTEGER, last_synced TEXT
        );
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            match_id INTEGER NOT NULL REFERENCES matches(id),
            prediction TEXT NOT NULL,
            points_earned INTEGER DEFAULT 0, is_correct INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, match_id)
        );
        CREATE TABLE IF NOT EXISTS special_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            competition_id INTEGER NOT NULL REFERENCES competitions(id),
            champion_team_id INTEGER REFERENCES teams(id),
            runner_up_team_id INTEGER REFERENCES teams(id),
            top_scorer_name TEXT,
            points_champion INTEGER DEFAULT 0, points_runner_up INTEGER DEFAULT 0,
            points_top_scorer INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, competition_id)
        );
        CREATE TABLE IF NOT EXISTS tournament_config (
            key TEXT PRIMARY KEY, value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, action TEXT NOT NULL, details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id);
        CREATE INDEX IF NOT EXISTS idx_bets_match ON bets(match_id);
        CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
        CREATE INDEX IF NOT EXISTS idx_matches_comp ON matches(competition_id);
    """)
    conn.commit()
    conn.close()


def migrate_db():
    """Agrega columnas nuevas si faltan (para upgrades sin perder datos)."""
    conn = get_db()
    mcols = {r[1] for r in conn.execute("PRAGMA table_info(matches)").fetchall()}
    for col, default in [("competition_id","1"),("penalty_home","NULL"),("penalty_away","NULL"),("decided_by_penalties","0")]:
        if col not in mcols:
            conn.execute(f"ALTER TABLE matches ADD COLUMN {col} INTEGER DEFAULT {default}")
    tcols = {r[1] for r in conn.execute("PRAGMA table_info(teams)").fetchall()}
    if "competition_id" not in tcols:
        conn.execute("ALTER TABLE teams ADD COLUMN competition_id INTEGER")
    spcols = {r[1] for r in conn.execute("PRAGMA table_info(special_predictions)").fetchall()}
    if "competition_id" not in spcols:
        conn.execute("ALTER TABLE special_predictions ADD COLUMN competition_id INTEGER DEFAULT 1")
    conn.execute("""CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL, short_name TEXT, season TEXT,
        is_active INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')))""")
    conn.commit(); conn.close()


# ─── Competitions ─────────────────────────────────────────────────────────────

def get_all_competitions(active_only=True):
    conn = get_db()
    q = "SELECT * FROM competitions" + (" WHERE is_active=1" if active_only else "") + " ORDER BY sort_order, id"
    r = conn.execute(q).fetchall(); conn.close(); return r

def get_competition(cid):
    conn = get_db(); c = conn.execute("SELECT * FROM competitions WHERE id=?", (cid,)).fetchone(); conn.close(); return c

def get_competition_by_code(code):
    conn = get_db(); c = conn.execute("SELECT * FROM competitions WHERE code=?", (code,)).fetchone(); conn.close(); return c

def create_competition(code, name, short_name=None, season=None, sort_order=0):
    conn = get_db()
    try:
        conn.execute("INSERT INTO competitions (code,name,short_name,season,sort_order) VALUES (?,?,?,?,?)",
                     (code, name, short_name or name, season, sort_order))
        conn.commit(); cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    except sqlite3.IntegrityError:
        cid = conn.execute("SELECT id FROM competitions WHERE code=?", (code,)).fetchone()["id"]
    conn.close(); return cid

def get_default_competition_id():
    comps = get_all_competitions()
    if comps: return comps[0]["id"]
    return create_competition("WORLD_CUP", "Mundial 2026", "Mundial", "2026", 1)


# ─── Users ────────────────────────────────────────────────────────────────────

def create_user(username, display_name, password, role="user", is_approved=0):
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username,display_name,password_hash,role,is_approved) VALUES (?,?,?,?,?)",
                     (username.lower(), display_name, generate_password_hash(password), role, is_approved))
        conn.commit(); return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def get_user_by_username(username):
    conn = get_db(); u = conn.execute("SELECT * FROM users WHERE username=?", (username.lower(),)).fetchone(); conn.close(); return u

def get_user_by_id(uid):
    conn = get_db(); u = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone(); conn.close(); return u

def verify_password(user_row, password):
    return check_password_hash(user_row["password_hash"], password)

def get_all_users(role="user"):
    conn = get_db(); r = conn.execute("SELECT * FROM users WHERE role=? ORDER BY created_at DESC", (role,)).fetchall(); conn.close(); return r

def update_user(uid, **kwargs):
    conn = get_db()
    for key, val in kwargs.items():
        if key == "password":
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(val), uid))
        elif key in ("is_approved","is_active","role","display_name"):
            conn.execute(f"UPDATE users SET {key}=? WHERE id=?", (val, uid))
    conn.commit(); conn.close()


# ─── Teams ────────────────────────────────────────────────────────────────────

def get_all_teams(competition_id=None):
    conn = get_db()
    if competition_id:
        r = conn.execute("SELECT * FROM teams WHERE competition_id=? ORDER BY name", (competition_id,)).fetchall()
    else:
        r = conn.execute("SELECT * FROM teams ORDER BY name").fetchall()
    conn.close(); return r

def get_team(tid):
    conn = get_db(); t = conn.execute("SELECT * FROM teams WHERE id=?", (tid,)).fetchone(); conn.close(); return t

def upsert_team(api_id=None, name="", code="", flag_url="", group_name="", competition_id=None):
    conn = get_db()
    if code and competition_id:
        ex = conn.execute("SELECT id FROM teams WHERE code=? AND competition_id=?", (code, competition_id)).fetchone()
        if ex:
            conn.execute("UPDATE teams SET name=?,flag_url=?,group_name=? WHERE id=?", (name, flag_url, group_name or None, ex["id"]))
            conn.commit(); conn.close(); return ex["id"], False
    if api_id:
        ex = conn.execute("SELECT id FROM teams WHERE api_id=?", (str(api_id),)).fetchone()
        if ex:
            conn.execute("UPDATE teams SET name=?,code=?,flag_url=?,group_name=?,competition_id=COALESCE(?,competition_id) WHERE id=?",
                         (name, code, flag_url, group_name or None, competition_id, ex["id"]))
            conn.commit(); conn.close(); return ex["id"], False
    conn.execute("INSERT INTO teams (api_id,name,code,flag_url,group_name,competition_id) VALUES (?,?,?,?,?,?)",
                 (str(api_id) if api_id else None, name, code, flag_url, group_name or None, competition_id))
    conn.commit(); tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]; conn.close(); return tid, True


# ─── Matches ──────────────────────────────────────────────────────────────────

def _match_query(extra="", params=None):
    return """SELECT m.*, ht.name as home_name, ht.code as home_code, ht.flag_url as home_flag,
           at.name as away_name, at.code as away_code, at.flag_url as away_flag,
           c.code as comp_code, c.short_name as comp_name
           FROM matches m LEFT JOIN teams ht ON m.home_team_id=ht.id
           LEFT JOIN teams at ON m.away_team_id=at.id
           LEFT JOIN competitions c ON m.competition_id=c.id """ + extra

def get_all_matches(competition_id=None, stage=None, group=None, status_filter=None):
    conn = get_db()
    q = _match_query("WHERE 1=1"); params = []
    if competition_id: q += " AND m.competition_id=?"; params.append(competition_id)
    if stage: q += " AND m.stage=?"; params.append(stage)
    if group: q += " AND m.group_name=?"; params.append(group)
    if status_filter == "upcoming": q += " AND m.status IN ('SCHEDULED','TIMED')"
    elif status_filter == "live": q += " AND m.status IN ('LIVE','IN_PLAY','PAUSED')"
    elif status_filter == "finished": q += " AND m.status='FINISHED'"
    q += " ORDER BY m.match_date"
    r = conn.execute(q, params).fetchall(); conn.close(); return r

def get_match(mid):
    conn = get_db(); m = conn.execute(_match_query("WHERE m.id=?"), (mid,)).fetchone(); conn.close(); return m

def create_match(home_team_id, away_team_id, match_date, stage="GROUP_STAGE",
                 group_name=None, venue=None, api_id=None, matchday=None, competition_id=None):
    conn = get_db(); comp_id = competition_id or get_default_competition_id()
    conn.execute("INSERT INTO matches (api_id,competition_id,home_team_id,away_team_id,match_date,stage,group_name,venue,matchday) VALUES (?,?,?,?,?,?,?,?,?)",
                 (api_id, comp_id, home_team_id, away_team_id, match_date, stage, group_name, venue, matchday))
    conn.commit(); conn.close()

def update_match_result(mid, home_score, away_score, status="FINISHED", penalty_home=None, penalty_away=None):
    conn = get_db()
    is_final = 1 if status == "FINISHED" else 0
    decided = 1 if (penalty_home is not None and penalty_away is not None) else 0
    conn.execute("UPDATE matches SET home_score=?,away_score=?,status=?,is_result_final=?,penalty_home=?,penalty_away=?,decided_by_penalties=? WHERE id=?",
                 (home_score, away_score, status, is_final, penalty_home, penalty_away, decided, mid))
    conn.commit(); conn.close()

def upsert_match_from_api(api_id, home_api_id, away_api_id, match_date, stage, group,
                           venue, status, home_score, away_score, matchday, competition_id=None):
    conn = get_db(); comp_id = competition_id or get_default_competition_id()
    ht = conn.execute("SELECT id FROM teams WHERE api_id=?", (str(home_api_id),)).fetchone() if home_api_id else None
    at = conn.execute("SELECT id FROM teams WHERE api_id=?", (str(away_api_id),)).fetchone() if away_api_id else None
    htid = ht["id"] if ht else None; atid = at["id"] if at else None
    now = datetime.now(timezone.utc).isoformat(); is_final = 1 if status == "FINISHED" else 0
    existing = conn.execute("SELECT id FROM matches WHERE api_id=?", (str(api_id),)).fetchone()
    if existing:
        conn.execute("""UPDATE matches SET home_team_id=COALESCE(?,home_team_id),away_team_id=COALESCE(?,away_team_id),
            match_date=?,stage=?,group_name=?,venue=?,status=?,home_score=COALESCE(?,home_score),
            away_score=COALESCE(?,away_score),is_result_final=?,matchday=?,last_synced=?,competition_id=? WHERE id=?""",
            (htid, atid, match_date, stage, group, venue, status, home_score, away_score, is_final, matchday, now, comp_id, existing["id"]))
    else:
        conn.execute("""INSERT INTO matches (api_id,competition_id,home_team_id,away_team_id,match_date,stage,group_name,
            venue,status,home_score,away_score,is_result_final,matchday,last_synced) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (str(api_id), comp_id, htid, atid, match_date, stage, group, venue, status, home_score, away_score, is_final, matchday, now))
    conn.commit(); conn.close()


# ─── Bets ─────────────────────────────────────────────────────────────────────

def get_user_bets(uid, competition_id=None):
    conn = get_db()
    q = """SELECT b.*, m.match_date, m.stage, m.status as match_status,
        m.home_score, m.away_score, m.is_result_final, m.competition_id,
        m.penalty_home, m.penalty_away, m.decided_by_penalties,
        ht.name as home_name, ht.flag_url as home_flag,
        at.name as away_name, at.flag_url as away_flag, c.short_name as comp_name
        FROM bets b JOIN matches m ON b.match_id=m.id
        LEFT JOIN teams ht ON m.home_team_id=ht.id LEFT JOIN teams at ON m.away_team_id=at.id
        LEFT JOIN competitions c ON m.competition_id=c.id WHERE b.user_id=?"""
    params = [uid]
    if competition_id: q += " AND m.competition_id=?"; params.append(competition_id)
    q += " ORDER BY m.match_date"
    r = conn.execute(q, params).fetchall(); conn.close(); return r

def get_user_bets_dict(uid, competition_id=None):
    return {b["match_id"]: b for b in get_user_bets(uid, competition_id)}

def place_bet(uid, match_id, prediction):
    conn = get_db(); now = datetime.now(timezone.utc).isoformat()
    ex = conn.execute("SELECT id FROM bets WHERE user_id=? AND match_id=?", (uid, match_id)).fetchone()
    if ex: conn.execute("UPDATE bets SET prediction=?,updated_at=? WHERE id=?", (prediction, now, ex["id"]))
    else: conn.execute("INSERT INTO bets (user_id,match_id,prediction,updated_at) VALUES (?,?,?,?)", (uid, match_id, prediction, now))
    conn.commit(); conn.close()

def get_all_bets(match_id=None, user_id=None, competition_id=None):
    conn = get_db()
    q = """SELECT b.*, u.display_name, u.username, m.match_date,
           m.home_score as m_home_score, m.away_score as m_away_score,
           m.penalty_home, m.penalty_away, m.decided_by_penalties,
           ht.name as home_name, at.name as away_name
           FROM bets b JOIN users u ON b.user_id=u.id JOIN matches m ON b.match_id=m.id
           LEFT JOIN teams ht ON m.home_team_id=ht.id LEFT JOIN teams at ON m.away_team_id=at.id WHERE 1=1"""
    params = []
    if match_id: q += " AND b.match_id=?"; params.append(match_id)
    if user_id: q += " AND b.user_id=?"; params.append(user_id)
    if competition_id: q += " AND m.competition_id=?"; params.append(competition_id)
    q += " ORDER BY m.match_date DESC"
    r = conn.execute(q, params).fetchall(); conn.close(); return r


# ─── Scoring ──────────────────────────────────────────────────────────────────

def get_match_result_code(home_score, away_score, **_):
    if home_score is None or away_score is None: return None
    if home_score > away_score: return "1"
    elif home_score < away_score: return "2"
    return "X"

def recalculate_all(competition_id=None):
    from flask import current_app
    pts_win = current_app.config.get("POINTS_CORRECT_WIN", 1)
    pts_draw = current_app.config.get("POINTS_CORRECT_DRAW", 2)
    conn = get_db()
    q = "SELECT id, home_score, away_score FROM matches WHERE is_result_final=1"
    params = []
    if competition_id: q += " AND competition_id=?"; params.append(competition_id)
    finished = conn.execute(q, params).fetchall(); updated = 0
    for m in finished:
        result = get_match_result_code(m["home_score"], m["away_score"])
        if not result: continue
        for b in conn.execute("SELECT id, prediction FROM bets WHERE match_id=?", (m["id"],)).fetchall():
            if b["prediction"] == result:
                pts = pts_draw if result == "X" else pts_win
                conn.execute("UPDATE bets SET points_earned=?,is_correct=1 WHERE id=?", (pts, b["id"]))
            else:
                conn.execute("UPDATE bets SET points_earned=0,is_correct=0 WHERE id=?", (b["id"],))
            updated += 1
    conn.commit(); conn.close(); return updated

def recalculate_specials(competition_id=None):
    from flask import current_app
    conn = get_db()
    champ = get_config("actual_champion_team_id"); runner = get_config("actual_runner_up_team_id"); scorer = get_config("actual_top_scorer_name")
    q = "SELECT * FROM special_predictions"; params = []
    if competition_id: q += " WHERE competition_id=?"; params.append(competition_id)
    preds = conn.execute(q, params).fetchall(); updated = 0
    for p in preds:
        pc = current_app.config["POINTS_CHAMPION"] if (champ and str(p["champion_team_id"]) == str(champ)) else 0
        pr = current_app.config["POINTS_RUNNER_UP"] if (runner and str(p["runner_up_team_id"]) == str(runner)) else 0
        ps = current_app.config["POINTS_TOP_SCORER"] if (scorer and p["top_scorer_name"] and p["top_scorer_name"].strip().lower() == scorer.strip().lower()) else 0
        conn.execute("UPDATE special_predictions SET points_champion=?,points_runner_up=?,points_top_scorer=? WHERE id=?", (pc, pr, ps, p["id"]))
        updated += 1
    conn.commit(); conn.close(); return updated


# ─── Special Predictions ──────────────────────────────────────────────────────

def get_special_prediction(uid, competition_id=None):
    conn = get_db()
    if competition_id:
        p = conn.execute("""SELECT sp.*, ct.name as champion_name, rt.name as runner_up_name FROM special_predictions sp
            LEFT JOIN teams ct ON sp.champion_team_id=ct.id LEFT JOIN teams rt ON sp.runner_up_team_id=rt.id
            WHERE sp.user_id=? AND sp.competition_id=?""", (uid, competition_id)).fetchone()
    else:
        p = conn.execute("""SELECT sp.*, ct.name as champion_name, rt.name as runner_up_name FROM special_predictions sp
            LEFT JOIN teams ct ON sp.champion_team_id=ct.id LEFT JOIN teams rt ON sp.runner_up_team_id=rt.id
            WHERE sp.user_id=? ORDER BY sp.id LIMIT 1""", (uid,)).fetchone()
    conn.close(); return p

def save_special_prediction(uid, champion_id, runner_up_id, top_scorer, competition_id=None):
    conn = get_db(); comp_id = competition_id or get_default_competition_id()
    now = datetime.now(timezone.utc).isoformat()
    ex = conn.execute("SELECT id FROM special_predictions WHERE user_id=? AND competition_id=?", (uid, comp_id)).fetchone()
    if ex:
        conn.execute("UPDATE special_predictions SET champion_team_id=?,runner_up_team_id=?,top_scorer_name=?,updated_at=? WHERE id=?",
            (champion_id or None, runner_up_id or None, top_scorer or None, now, ex["id"]))
    else:
        conn.execute("INSERT INTO special_predictions (user_id,competition_id,champion_team_id,runner_up_team_id,top_scorer_name) VALUES (?,?,?,?,?)",
            (uid, comp_id, champion_id or None, runner_up_id or None, top_scorer or None))
    conn.commit(); conn.close()


# ─── Config / Audit ───────────────────────────────────────────────────────────

def get_config(key, default=None):
    conn = get_db(); r = conn.execute("SELECT value FROM tournament_config WHERE key=?", (key,)).fetchone(); conn.close()
    return r["value"] if r else default

def set_config(key, value):
    conn = get_db(); conn.execute("INSERT OR REPLACE INTO tournament_config (key,value,updated_at) VALUES (?,?,datetime('now'))", (key, str(value)))
    conn.commit(); conn.close()

def audit_log(user_id, action, details=""):
    conn = get_db(); conn.execute("INSERT INTO audit_log (user_id,action,details) VALUES (?,?,?)", (user_id, action, details))
    conn.commit(); conn.close()

def get_recent_logs(limit=20):
    conn = get_db()
    r = conn.execute("SELECT a.*, u.display_name FROM audit_log a LEFT JOIN users u ON a.user_id=u.id ORDER BY a.created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return r


# ─── Ranking ──────────────────────────────────────────────────────────────────

def get_ranking(competition_id=None):
    conn = get_db()
    users = conn.execute("SELECT * FROM users WHERE is_approved=1 AND role='user'").fetchall()
    ranking = []
    for u in users:
        if competition_id:
            bets = conn.execute("SELECT b.* FROM bets b JOIN matches m ON b.match_id=m.id WHERE b.user_id=? AND m.competition_id=?", (u["id"], competition_id)).fetchall()
            sp = conn.execute("SELECT * FROM special_predictions WHERE user_id=? AND competition_id=?", (u["id"], competition_id)).fetchone()
        else:
            bets = conn.execute("SELECT * FROM bets WHERE user_id=?", (u["id"],)).fetchall()
            sp = None
        match_pts = sum(b["points_earned"] for b in bets)
        total_bets = len(bets); correct = sum(1 for b in bets if b["is_correct"] == 1)
        draws_correct = sum(1 for b in bets if b["is_correct"] == 1 and b["prediction"] == "X")
        accuracy = round(correct / total_bets * 100, 1) if total_bets > 0 else 0
        pc = sp["points_champion"] if sp else 0; pr = sp["points_runner_up"] if sp else 0; ps = sp["points_top_scorer"] if sp else 0
        if not competition_id:
            for s in conn.execute("SELECT * FROM special_predictions WHERE user_id=?", (u["id"],)).fetchall():
                pc += s["points_champion"]; pr += s["points_runner_up"]; ps += s["points_top_scorer"]
        ranking.append({"user_id": u["id"], "display_name": u["display_name"], "username": u["username"],
            "total_points": match_pts + pc + pr + ps, "match_points": match_pts,
            "pts_champion": pc, "pts_runner_up": pr, "pts_top_scorer": ps,
            "total_bets": total_bets, "correct_bets": correct, "draw_correct": draws_correct,
            "accuracy": accuracy, "created_at": u["created_at"]})
    conn.close()
    ranking.sort(key=lambda x: (-x["total_points"], -x["draw_correct"], -x["correct_bets"], -x["accuracy"], x["created_at"]))
    for i, r in enumerate(ranking): r["position"] = i + 1
    return ranking

def ensure_admin(username, password, display_name):
    if not get_user_by_username(username):
        create_user(username, display_name, password, role="admin", is_approved=1)
        print(f"  ✓ Admin creado: {username}")
