"""
Capa de base de datos con sqlite3 puro.
Sin ORM - simple, directo, sin dependencias externas.
"""
import sqlite3
import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "mundial2026.db"))


def get_db():
    """Retorna conexión a SQLite con row_factory para acceso por nombre."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Crea todas las tablas si no existen."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_approved INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id TEXT UNIQUE,
            name TEXT NOT NULL,
            code TEXT,
            flag_url TEXT,
            group_name TEXT
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id TEXT UNIQUE,
            home_team_id INTEGER REFERENCES teams(id),
            away_team_id INTEGER REFERENCES teams(id),
            match_date TEXT NOT NULL,
            stage TEXT,
            group_name TEXT,
            venue TEXT,
            status TEXT DEFAULT 'SCHEDULED',
            home_score INTEGER,
            away_score INTEGER,
            is_result_final INTEGER DEFAULT 0,
            matchday INTEGER,
            last_synced TEXT
        );

        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            match_id INTEGER NOT NULL REFERENCES matches(id),
            prediction TEXT NOT NULL,
            points_earned INTEGER DEFAULT 0,
            is_correct INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, match_id)
        );

        CREATE TABLE IF NOT EXISTS special_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            champion_team_id INTEGER REFERENCES teams(id),
            runner_up_team_id INTEGER REFERENCES teams(id),
            top_scorer_name TEXT,
            points_champion INTEGER DEFAULT 0,
            points_runner_up INTEGER DEFAULT 0,
            points_top_scorer INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tournament_config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id);
        CREATE INDEX IF NOT EXISTS idx_bets_match ON bets(match_id);
        CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
    """)
    conn.commit()
    conn.close()


# ─── User operations ─────────────────────────────────────────────────────────

def create_user(username, display_name, password, role="user", is_approved=0):
    conn = get_db()
    pw_hash = generate_password_hash(password)
    try:
        conn.execute(
            "INSERT INTO users (username, display_name, password_hash, role, is_approved) VALUES (?,?,?,?,?)",
            (username.lower(), display_name, pw_hash, role, is_approved)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username.lower(),)).fetchone()
    conn.close()
    return user


def get_user_by_id(uid):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return user


def verify_password(user_row, password):
    return check_password_hash(user_row["password_hash"], password)


def get_all_users(role="user"):
    conn = get_db()
    users = conn.execute("SELECT * FROM users WHERE role=? ORDER BY created_at DESC", (role,)).fetchall()
    conn.close()
    return users


def update_user(uid, **kwargs):
    conn = get_db()
    for key, val in kwargs.items():
        if key == "password":
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(val), uid))
        elif key in ("is_approved", "is_active", "role", "display_name"):
            conn.execute(f"UPDATE users SET {key}=? WHERE id=?", (val, uid))
    conn.commit()
    conn.close()


# ─── Teams ────────────────────────────────────────────────────────────────────

def get_all_teams():
    conn = get_db()
    teams = conn.execute("SELECT * FROM teams ORDER BY name").fetchall()
    conn.close()
    return teams


def get_team(tid):
    conn = get_db()
    t = conn.execute("SELECT * FROM teams WHERE id=?", (tid,)).fetchone()
    conn.close()
    return t


def upsert_team(api_id=None, name="", code="", flag_url="", group_name=""):
    conn = get_db()
    if api_id:
        existing = conn.execute("SELECT id FROM teams WHERE api_id=?", (str(api_id),)).fetchone()
        if existing:
            conn.execute("UPDATE teams SET name=?,code=?,flag_url=?,group_name=? WHERE api_id=?",
                         (name, code, flag_url, group_name or None, str(api_id)))
            conn.commit()
            tid = existing["id"]
            conn.close()
            return tid, False
    conn.execute("INSERT INTO teams (api_id,name,code,flag_url,group_name) VALUES (?,?,?,?,?)",
                 (str(api_id) if api_id else None, name, code, flag_url, group_name or None))
    conn.commit()
    tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return tid, True


def get_team_by_api_id(api_id):
    conn = get_db()
    t = conn.execute("SELECT * FROM teams WHERE api_id=?", (str(api_id),)).fetchone()
    conn.close()
    return t


# ─── Matches ──────────────────────────────────────────────────────────────────

def get_all_matches(stage=None, group=None, status_filter=None):
    conn = get_db()
    q = """SELECT m.*, 
           ht.name as home_name, ht.code as home_code, ht.flag_url as home_flag,
           at.name as away_name, at.code as away_code, at.flag_url as away_flag
           FROM matches m
           LEFT JOIN teams ht ON m.home_team_id=ht.id
           LEFT JOIN teams at ON m.away_team_id=at.id WHERE 1=1"""
    params = []
    if stage:
        q += " AND m.stage=?"
        params.append(stage)
    if group:
        q += " AND m.group_name=?"
        params.append(group)
    if status_filter == "upcoming":
        q += " AND m.status IN ('SCHEDULED','TIMED')"
    elif status_filter == "live":
        q += " AND m.status IN ('LIVE','IN_PLAY','PAUSED')"
    elif status_filter == "finished":
        q += " AND m.status='FINISHED'"
    q += " ORDER BY m.match_date"
    matches = conn.execute(q, params).fetchall()
    conn.close()
    return matches


def get_match(mid):
    conn = get_db()
    m = conn.execute("""SELECT m.*, 
        ht.name as home_name, ht.code as home_code, ht.flag_url as home_flag,
        at.name as away_name, at.code as away_code, at.flag_url as away_flag
        FROM matches m
        LEFT JOIN teams ht ON m.home_team_id=ht.id
        LEFT JOIN teams at ON m.away_team_id=at.id
        WHERE m.id=?""", (mid,)).fetchone()
    conn.close()
    return m


def create_match(home_team_id, away_team_id, match_date, stage="GROUP_STAGE",
                 group_name=None, venue=None, api_id=None, matchday=None):
    conn = get_db()
    conn.execute("""INSERT INTO matches (api_id,home_team_id,away_team_id,match_date,stage,group_name,venue,matchday)
                    VALUES (?,?,?,?,?,?,?,?)""",
                 (api_id, home_team_id, away_team_id, match_date, stage, group_name, venue, matchday))
    conn.commit()
    conn.close()


def update_match_result(mid, home_score, away_score, status="FINISHED"):
    conn = get_db()
    is_final = 1 if status == "FINISHED" else 0
    conn.execute("UPDATE matches SET home_score=?,away_score=?,status=?,is_result_final=? WHERE id=?",
                 (home_score, away_score, status, is_final, mid))
    conn.commit()
    conn.close()


def upsert_match_from_api(api_id, home_api_id, away_api_id, match_date, stage, group,
                           venue, status, home_score, away_score, matchday):
    conn = get_db()
    ht = conn.execute("SELECT id FROM teams WHERE api_id=?", (str(home_api_id),)).fetchone() if home_api_id else None
    at = conn.execute("SELECT id FROM teams WHERE api_id=?", (str(away_api_id),)).fetchone() if away_api_id else None
    htid = ht["id"] if ht else None
    atid = at["id"] if at else None
    
    existing = conn.execute("SELECT id FROM matches WHERE api_id=?", (str(api_id),)).fetchone()
    now = datetime.now(timezone.utc).isoformat()
    is_final = 1 if status == "FINISHED" else 0
    
    if existing:
        conn.execute("""UPDATE matches SET home_team_id=COALESCE(?,home_team_id),
            away_team_id=COALESCE(?,away_team_id), match_date=?, stage=?, group_name=?,
            venue=?, status=?, home_score=COALESCE(?,home_score), away_score=COALESCE(?,away_score),
            is_result_final=?, matchday=?, last_synced=? WHERE api_id=?""",
            (htid, atid, match_date, stage, group, venue, status, home_score, away_score,
             is_final, matchday, now, str(api_id)))
    else:
        conn.execute("""INSERT INTO matches (api_id,home_team_id,away_team_id,match_date,stage,
            group_name,venue,status,home_score,away_score,is_result_final,matchday,last_synced)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (str(api_id), htid, atid, match_date, stage, group, venue, status,
             home_score, away_score, is_final, matchday, now))
    conn.commit()
    conn.close()


# ─── Bets ─────────────────────────────────────────────────────────────────────

def get_user_bets(uid):
    conn = get_db()
    bets = conn.execute("""SELECT b.*, m.match_date, m.stage, m.status as match_status,
        m.home_score, m.away_score, m.is_result_final,
        ht.name as home_name, ht.flag_url as home_flag,
        at.name as away_name, at.flag_url as away_flag
        FROM bets b JOIN matches m ON b.match_id=m.id
        LEFT JOIN teams ht ON m.home_team_id=ht.id
        LEFT JOIN teams at ON m.away_team_id=at.id
        WHERE b.user_id=? ORDER BY m.match_date""", (uid,)).fetchall()
    conn.close()
    return bets


def get_user_bets_dict(uid):
    """Returns dict of match_id -> bet row."""
    bets = get_user_bets(uid)
    return {b["match_id"]: b for b in bets}


def place_bet(uid, match_id, prediction):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    existing = conn.execute("SELECT id FROM bets WHERE user_id=? AND match_id=?", (uid, match_id)).fetchone()
    if existing:
        conn.execute("UPDATE bets SET prediction=?, updated_at=? WHERE id=?", (prediction, now, existing["id"]))
    else:
        conn.execute("INSERT INTO bets (user_id,match_id,prediction,updated_at) VALUES (?,?,?,?)",
                     (uid, match_id, prediction, now))
    conn.commit()
    conn.close()


def get_all_bets(match_id=None, user_id=None):
    conn = get_db()
    q = """SELECT b.*, u.display_name, u.username,
           m.match_date, m.home_score as m_home_score, m.away_score as m_away_score,
           ht.name as home_name, at.name as away_name
           FROM bets b JOIN users u ON b.user_id=u.id
           JOIN matches m ON b.match_id=m.id
           LEFT JOIN teams ht ON m.home_team_id=ht.id
           LEFT JOIN teams at ON m.away_team_id=at.id WHERE 1=1"""
    params = []
    if match_id:
        q += " AND b.match_id=?"
        params.append(match_id)
    if user_id:
        q += " AND b.user_id=?"
        params.append(user_id)
    q += " ORDER BY m.match_date DESC"
    bets = conn.execute(q, params).fetchall()
    conn.close()
    return bets


# ─── Scoring ──────────────────────────────────────────────────────────────────

def get_match_result_code(home_score, away_score):
    if home_score is None or away_score is None:
        return None
    if home_score > away_score:
        return "1"
    elif home_score == away_score:
        return "X"
    return "2"


def recalculate_all():
    """Recalcula puntos de TODAS las apuestas de partidos finalizados."""
    from flask import current_app
    pts_win = current_app.config.get("POINTS_CORRECT_WIN", 1)
    pts_draw = current_app.config.get("POINTS_CORRECT_DRAW", 2)
    
    conn = get_db()
    finished = conn.execute("SELECT id, home_score, away_score FROM matches WHERE is_result_final=1").fetchall()
    updated = 0
    for m in finished:
        result = get_match_result_code(m["home_score"], m["away_score"])
        if not result:
            continue
        bets = conn.execute("SELECT id, prediction FROM bets WHERE match_id=?", (m["id"],)).fetchall()
        for b in bets:
            if b["prediction"] == result:
                pts = pts_draw if result == "X" else pts_win
                conn.execute("UPDATE bets SET points_earned=?, is_correct=1 WHERE id=?", (pts, b["id"]))
            else:
                conn.execute("UPDATE bets SET points_earned=0, is_correct=0 WHERE id=?", (b["id"],))
            updated += 1
    conn.commit()
    conn.close()
    return updated


def recalculate_specials():
    """Recalcula pronósticos especiales si hay resultados reales."""
    from flask import current_app
    conn = get_db()
    actual_champ = get_config("actual_champion_team_id")
    actual_runner = get_config("actual_runner_up_team_id")
    actual_scorer = get_config("actual_top_scorer_name")
    
    preds = conn.execute("SELECT * FROM special_predictions").fetchall()
    updated = 0
    for p in preds:
        pc = current_app.config["POINTS_CHAMPION"] if (actual_champ and str(p["champion_team_id"]) == str(actual_champ)) else 0
        pr = current_app.config["POINTS_RUNNER_UP"] if (actual_runner and str(p["runner_up_team_id"]) == str(actual_runner)) else 0
        ps = 0
        if actual_scorer and p["top_scorer_name"]:
            if p["top_scorer_name"].strip().lower() == actual_scorer.strip().lower():
                ps = current_app.config["POINTS_TOP_SCORER"]
        conn.execute("UPDATE special_predictions SET points_champion=?,points_runner_up=?,points_top_scorer=? WHERE id=?",
                     (pc, pr, ps, p["id"]))
        updated += 1
    conn.commit()
    conn.close()
    return updated


# ─── Special Predictions ──────────────────────────────────────────────────────

def get_special_prediction(uid):
    conn = get_db()
    p = conn.execute("""SELECT sp.*, ct.name as champion_name, rt.name as runner_up_name
        FROM special_predictions sp
        LEFT JOIN teams ct ON sp.champion_team_id=ct.id
        LEFT JOIN teams rt ON sp.runner_up_team_id=rt.id
        WHERE sp.user_id=?""", (uid,)).fetchone()
    conn.close()
    return p


def save_special_prediction(uid, champion_id, runner_up_id, top_scorer):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    existing = conn.execute("SELECT id FROM special_predictions WHERE user_id=?", (uid,)).fetchone()
    if existing:
        conn.execute("""UPDATE special_predictions SET champion_team_id=?,runner_up_team_id=?,
            top_scorer_name=?,updated_at=? WHERE user_id=?""",
            (champion_id or None, runner_up_id or None, top_scorer or None, now, uid))
    else:
        conn.execute("""INSERT INTO special_predictions (user_id,champion_team_id,runner_up_team_id,top_scorer_name)
            VALUES (?,?,?,?)""", (uid, champion_id or None, runner_up_id or None, top_scorer or None))
    conn.commit()
    conn.close()


# ─── Config ───────────────────────────────────────────────────────────────────

def get_config(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM tournament_config WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_config(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO tournament_config (key,value,updated_at) VALUES (?,?,datetime('now'))",
                 (key, str(value)))
    conn.commit()
    conn.close()


# ─── Audit ────────────────────────────────────────────────────────────────────

def audit_log(user_id, action, details=""):
    conn = get_db()
    conn.execute("INSERT INTO audit_log (user_id,action,details) VALUES (?,?,?)", (user_id, action, details))
    conn.commit()
    conn.close()


def get_recent_logs(limit=20):
    conn = get_db()
    logs = conn.execute("""SELECT a.*, u.display_name FROM audit_log a
        LEFT JOIN users u ON a.user_id=u.id ORDER BY a.created_at DESC LIMIT ?""", (limit,)).fetchall()
    conn.close()
    return logs


# ─── Ranking ──────────────────────────────────────────────────────────────────

def get_ranking():
    conn = get_db()
    users = conn.execute("SELECT * FROM users WHERE is_approved=1 AND role='user'").fetchall()
    ranking = []
    for u in users:
        bets = conn.execute("SELECT * FROM bets WHERE user_id=?", (u["id"],)).fetchall()
        match_pts = sum(b["points_earned"] for b in bets)
        total_bets = len(bets)
        correct = sum(1 for b in bets if b["is_correct"] == 1)
        draws_correct = sum(1 for b in bets if b["is_correct"] == 1 and b["prediction"] == "X")
        accuracy = round(correct / total_bets * 100, 1) if total_bets > 0 else 0

        sp = conn.execute("SELECT * FROM special_predictions WHERE user_id=?", (u["id"],)).fetchone()
        pc = sp["points_champion"] if sp else 0
        pr = sp["points_runner_up"] if sp else 0
        ps = sp["points_top_scorer"] if sp else 0
        
        ranking.append({
            "user_id": u["id"], "display_name": u["display_name"], "username": u["username"],
            "total_points": match_pts + pc + pr + ps, "match_points": match_pts,
            "pts_champion": pc, "pts_runner_up": pr, "pts_top_scorer": ps,
            "total_bets": total_bets, "correct_bets": correct, "draw_correct": draws_correct,
            "accuracy": accuracy, "created_at": u["created_at"],
        })
    conn.close()
    ranking.sort(key=lambda x: (-x["total_points"], -x["draw_correct"], -x["correct_bets"], -x["accuracy"], x["created_at"]))
    for i, r in enumerate(ranking):
        r["position"] = i + 1
    return ranking


# ─── Init admin ───────────────────────────────────────────────────────────────

def ensure_admin(username, password, display_name):
    if not get_user_by_username(username):
        create_user(username, display_name, password, role="admin", is_approved=1)
        print(f"  ✓ Admin creado: {username}")
