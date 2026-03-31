"""
🏆 Mundial 2026 — Aplicación de Pronósticos
Flask + SQLite3 puro. Sin ORM, sin dependencias pesadas.
"""
import os
import re
import functools
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, abort
)

import database as db

# ═══════════════════════════════════════════════════════════════════════════════
# App Factory
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mundial2026-dev-key-cambiar!")

# Config
app.config.update(
    ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "admin"),
    ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "admin2026!"),
    ADMIN_DISPLAY_NAME=os.environ.get("ADMIN_DISPLAY_NAME", "Administrador"),
    BET_LOCK_MINUTES=int(os.environ.get("BET_LOCK_MINUTES", "10")),
    POINTS_CORRECT_WIN=int(os.environ.get("POINTS_CORRECT_WIN", "1")),
    POINTS_CORRECT_DRAW=int(os.environ.get("POINTS_CORRECT_DRAW", "2")),
    POINTS_CHAMPION=int(os.environ.get("POINTS_CHAMPION", "10")),
    POINTS_RUNNER_UP=int(os.environ.get("POINTS_RUNNER_UP", "5")),
    POINTS_TOP_SCORER=int(os.environ.get("POINTS_TOP_SCORER", "7")),
    SPECIAL_PREDICTIONS_LOCK=os.environ.get("SPECIAL_PREDICTIONS_LOCK", "2026-06-11T16:00:00+00:00"),
    DISPLAY_TIMEZONE=os.environ.get("DISPLAY_TIMEZONE", "America/Santiago"),
    FOOTBALL_API_KEY=os.environ.get("FOOTBALL_API_KEY", ""),
)

# ═══════════════════════════════════════════════════════════════════════════════
# Auth helpers
# ═══════════════════════════════════════════════════════════════════════════════

@app.before_request
def load_current_user():
    """Carga el usuario actual en g desde la sesión."""
    g.user = None
    uid = session.get("user_id")
    if uid:
        g.user = db.get_user_by_id(uid)
        if g.user and not g.user["is_active"]:
            session.clear()
            g.user = None


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not g.user:
            flash("Inicia sesión para continuar.", "info")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if g.user["role"] != "admin":
            flash("No tienes permiso para esta sección.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════════════════════
# Template helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _tz_offset():
    """Offset en horas para la zona configurada (simplificado, sin pytz)."""
    tz = app.config["DISPLAY_TIMEZONE"]
    offsets = {
        "America/Santiago": -4, "America/Bogota": -5, "America/Mexico_City": -6,
        "America/Lima": -5, "America/Buenos_Aires": -3, "America/New_York": -4,
        "America/Chicago": -5, "America/Los_Angeles": -7, "America/Sao_Paulo": -3,
        "Europe/Madrid": 2, "Europe/London": 1, "UTC": 0,
    }
    return offsets.get(tz, -4)


@app.template_filter("format_date")
def format_date_filter(dt_str, fmt="%d/%m/%Y %H:%M"):
    if not dt_str:
        return ""
    try:
        if isinstance(dt_str, str):
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            dt = dt_str
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt + timedelta(hours=_tz_offset())
        return local.strftime(fmt)
    except Exception:
        return str(dt_str)[:16]


@app.template_filter("format_time")
def format_time_filter(dt_str):
    return format_date_filter(dt_str, "%H:%M")


@app.template_filter("format_day")
def format_day_filter(dt_str):
    return format_date_filter(dt_str, "%A %d de %B %Y")


def is_match_locked(match_date_str):
    """True si el partido está bloqueado para apuestas."""
    try:
        if isinstance(match_date_str, str):
            md = datetime.fromisoformat(match_date_str.replace("Z", "+00:00"))
        else:
            md = match_date_str
        if md.tzinfo is None:
            md = md.replace(tzinfo=timezone.utc)
        lock_time = md - timedelta(minutes=app.config["BET_LOCK_MINUTES"])
        return datetime.now(timezone.utc) >= lock_time
    except Exception:
        return True


app.jinja_env.globals["is_match_locked"] = is_match_locked
app.jinja_env.globals["now_utc"] = lambda: datetime.now(timezone.utc)

STAGE_NAMES = {
    "GROUP_STAGE": "Fase de Grupos", "ROUND_OF_16": "Octavos de Final",
    "QUARTER_FINALS": "Cuartos de Final", "SEMI_FINALS": "Semifinales",
    "THIRD_PLACE": "Tercer Puesto", "FINAL": "Final",
}
app.jinja_env.globals["STAGE_NAMES"] = STAGE_NAMES


# ═══════════════════════════════════════════════════════════════════════════════
# Auth Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = db.get_user_by_username(username)
        if not user or not db.verify_password(user, password):
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template("auth/login.html")
        if not user["is_active"]:
            flash("Tu cuenta está desactivada.", "error")
            return render_template("auth/login.html")
        session["user_id"] = user["id"]
        session.permanent = True
        db.audit_log(user["id"], "LOGIN")
        return redirect(url_for("dashboard"))
    return render_template("auth/login.html")


@app.route("/registro", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password_confirm", "")
        errors = []
        if len(display_name) < 2: errors.append("Nombre debe tener al menos 2 caracteres.")
        if len(username) < 3: errors.append("Usuario debe tener al menos 3 caracteres.")
        if not re.match(r"^[a-z0-9_]+$", username): errors.append("Solo letras, números y _.")
        if len(password) < 6: errors.append("Contraseña: mínimo 6 caracteres.")
        if password != password2: errors.append("Las contraseñas no coinciden.")
        if db.get_user_by_username(username): errors.append("Ese usuario ya existe.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("auth/register.html", display_name=display_name, username=username)
        db.create_user(username, display_name, password)
        flash("¡Registro exitoso! Un admin debe aprobar tu cuenta.", "success")
        return redirect(url_for("login"))
    return render_template("auth/register.html")


@app.route("/logout")
def logout():
    if g.user:
        db.audit_log(g.user["id"], "LOGOUT")
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# ═══════════════════════════════════════════════════════════════════════════════
# Main Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
@login_required
def dashboard():
    now = datetime.now(timezone.utc).isoformat()
    all_m = db.get_all_matches()
    upcoming = [m for m in all_m if m["match_date"] > now and m["status"] in ("SCHEDULED", "TIMED", None)][:6]
    live = [m for m in all_m if m["status"] in ("LIVE", "IN_PLAY", "PAUSED")]
    recent = [m for m in all_m if m["is_result_final"]]
    recent.reverse()
    recent = recent[:4]
    
    my_bets = db.get_user_bets_dict(g.user["id"])
    ranking = db.get_ranking()[:5]
    my_rank = next((r for r in db.get_ranking() if r["user_id"] == g.user["id"]), None)
    
    total_pts = sum(b["points_earned"] for b in my_bets.values())
    sp = db.get_special_prediction(g.user["id"])
    if sp:
        total_pts += sp["points_champion"] + sp["points_runner_up"] + sp["points_top_scorer"]
    
    return render_template("dashboard.html", upcoming=upcoming, live_matches=live,
        recent_results=recent, my_bets=my_bets, ranking=ranking, my_rank=my_rank,
        total_points=total_pts, total_bets=len(my_bets))


@app.route("/partidos")
@login_required
def matches():
    stage = request.args.get("stage", "")
    group = request.args.get("group", "")
    status = request.args.get("status", "")
    all_matches = db.get_all_matches(stage=stage or None, group=group or None, status_filter=status or None)
    my_bets = db.get_user_bets_dict(g.user["id"])
    
    conn = db.get_db()
    stages = [r[0] for r in conn.execute("SELECT DISTINCT stage FROM matches WHERE stage IS NOT NULL ORDER BY stage").fetchall()]
    groups = [r[0] for r in conn.execute("SELECT DISTINCT group_name FROM matches WHERE group_name IS NOT NULL ORDER BY group_name").fetchall()]
    conn.close()
    
    return render_template("matches.html", matches=all_matches, my_bets=my_bets,
        stages=stages, groups=groups, current_stage=stage, current_group=group, current_status=status)


@app.route("/apostar/<int:match_id>", methods=["POST"])
@login_required
def place_bet(match_id):
    if not g.user["is_approved"]:
        flash("Tu cuenta no está aprobada.", "error")
        return redirect(url_for("matches"))
    m = db.get_match(match_id)
    if not m:
        abort(404)
    if is_match_locked(m["match_date"]):
        flash("Partido bloqueado para apuestas.", "error")
        return redirect(url_for("matches"))
    pred = request.form.get("prediction", "")
    if pred not in ("1", "X", "2"):
        flash("Predicción inválida.", "error")
        return redirect(url_for("matches"))
    db.place_bet(g.user["id"], match_id, pred)
    labels = {"1": "Local", "X": "Empate", "2": "Visita"}
    home = m["home_name"] or "Local"
    away = m["away_name"] or "Visita"
    flash(f"Apuesta: {home} vs {away} → {labels[pred]}", "success")
    return redirect(request.referrer or url_for("matches"))


@app.route("/ranking")
@login_required
def ranking():
    return render_template("ranking.html", ranking=db.get_ranking())


@app.route("/usuario/<int:uid>")
@login_required
def user_detail(uid):
    user = db.get_user_by_id(uid)
    if not user:
        abort(404)
    bets = db.get_user_bets(uid)
    sp = db.get_special_prediction(uid)
    return render_template("user_detail.html", user=user, bets=bets, special=sp)


@app.route("/mi-perfil")
@login_required
def my_profile():
    return redirect(url_for("user_detail", uid=g.user["id"]))


@app.route("/pronosticos-especiales", methods=["GET", "POST"])
@login_required
def special_predictions():
    if not g.user["is_approved"]:
        flash("Tu cuenta no está aprobada.", "error")
        return redirect(url_for("dashboard"))
    
    lock_str = db.get_config("special_predictions_lock", app.config["SPECIAL_PREDICTIONS_LOCK"])
    try:
        lock_date = datetime.fromisoformat(lock_str)
    except Exception:
        lock_date = datetime(2026, 6, 11, 16, 0, tzinfo=timezone.utc)
    is_locked = datetime.now(timezone.utc) >= lock_date
    
    teams = db.get_all_teams()
    pred = db.get_special_prediction(g.user["id"])
    
    if request.method == "POST" and not is_locked:
        champ = request.form.get("champion_team_id", type=int)
        runner = request.form.get("runner_up_team_id", type=int)
        scorer = request.form.get("top_scorer_name", "").strip()
        if champ and runner and champ == runner:
            flash("Campeón y subcampeón deben ser diferentes.", "error")
            return redirect(url_for("special_predictions"))
        db.save_special_prediction(g.user["id"], champ, runner, scorer)
        flash("Pronósticos especiales guardados.", "success")
        return redirect(url_for("special_predictions"))
    
    return render_template("special_predictions.html", teams=teams, prediction=pred,
                           is_locked=is_locked, lock_date=lock_date.isoformat())


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = db.get_db()
    pending = conn.execute("SELECT COUNT(*) FROM users WHERE is_approved=0 AND role='user'").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    total_matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    finished = conn.execute("SELECT COUNT(*) FROM matches WHERE is_result_final=1").fetchone()[0]
    total_bets = conn.execute("SELECT COUNT(*) FROM bets").fetchone()[0]
    conn.close()
    logs = db.get_recent_logs()
    return render_template("admin/dashboard.html", pending_users=pending, total_users=total_users,
        total_matches=total_matches, finished_matches=finished, total_bets=total_bets, recent_logs=logs)


@app.route("/admin/usuarios")
@admin_required
def admin_users():
    users = db.get_all_users()
    return render_template("admin/users.html", users=users)


@app.route("/admin/usuarios/<int:uid>/aprobar", methods=["POST"])
@admin_required
def approve_user(uid):
    db.update_user(uid, is_approved=1)
    db.audit_log(g.user["id"], "APPROVE_USER", f"uid={uid}")
    flash("Usuario aprobado.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/usuarios/<int:uid>/rechazar", methods=["POST"])
@admin_required
def reject_user(uid):
    db.update_user(uid, is_approved=0)
    db.audit_log(g.user["id"], "REJECT_USER", f"uid={uid}")
    flash("Aprobación revocada.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/usuarios/<int:uid>/toggle", methods=["POST"])
@admin_required
def toggle_user(uid):
    user = db.get_user_by_id(uid)
    new_state = 0 if user["is_active"] else 1
    db.update_user(uid, is_active=new_state)
    db.audit_log(g.user["id"], "TOGGLE_USER", f"uid={uid} active={new_state}")
    flash("Estado actualizado.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/usuarios/<int:uid>/reset-password", methods=["POST"])
@admin_required
def reset_password(uid):
    new_pw = request.form.get("new_password", "").strip()
    if len(new_pw) < 6:
        flash("Mínimo 6 caracteres.", "error")
        return redirect(url_for("admin_users"))
    db.update_user(uid, password=new_pw)
    db.audit_log(g.user["id"], "RESET_PASSWORD", f"uid={uid}")
    flash("Contraseña actualizada.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/apuestas")
@admin_required
def admin_bets():
    mid = request.args.get("match_id", type=int)
    uid = request.args.get("user_id", type=int)
    bets = db.get_all_bets(match_id=mid, user_id=uid)
    all_m = db.get_all_matches()
    users = db.get_all_users()
    return render_template("admin/bets.html", bets=bets, matches=all_m, users=users,
                           selected_match=mid, selected_user=uid)


@app.route("/admin/sincronizar")
@admin_required
def admin_sync():
    conn = db.get_db()
    tc = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    mc = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    conn.close()
    api_key = app.config.get("FOOTBALL_API_KEY", "")
    return render_template("admin/sync.html", teams_count=tc, matches_count=mc,
                           api_connected=bool(api_key), api_provider="football-data" if api_key else "manual")


@app.route("/admin/sincronizar/equipos", methods=["POST"])
@admin_required
def sync_teams():
    from api_service import get_provider
    try:
        provider = get_provider(app.config)
        teams = provider.fetch_teams("WC")
        c, u = 0, 0
        for t in teams:
            _, created = db.upsert_team(api_id=t.api_id, name=t.name, code=t.code,
                                         flag_url=t.flag_url, group_name=t.group)
            if created:
                c += 1
            else:
                u += 1
        db.audit_log(g.user["id"], "SYNC_TEAMS", f"new={c} updated={u}")
        flash(f"Equipos sincronizados: {c} nuevos, {u} actualizados.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_sync"))


@app.route("/admin/sincronizar/partidos", methods=["POST"])
@admin_required
def sync_matches():
    from api_service import get_provider
    try:
        provider = get_provider(app.config)
        matches = provider.fetch_matches("WC")
        for m in matches:
            db.upsert_match_from_api(m.api_id, m.home_team_api_id, m.away_team_api_id,
                m.match_date.isoformat() if hasattr(m.match_date, 'isoformat') else m.match_date,
                m.stage, m.group, m.venue, m.status, m.home_score, m.away_score, m.matchday)
        db.audit_log(g.user["id"], "SYNC_MATCHES", f"total={len(matches)}")
        flash(f"Partidos sincronizados: {len(matches)}.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_sync"))


@app.route("/admin/sincronizar/resultados", methods=["POST"])
@admin_required
def sync_results():
    from api_service import get_provider
    try:
        provider = get_provider(app.config)
        matches = provider.fetch_match_results("WC")
        for m in matches:
            db.upsert_match_from_api(m.api_id, m.home_team_api_id, m.away_team_api_id,
                m.match_date.isoformat() if hasattr(m.match_date, 'isoformat') else m.match_date,
                m.stage, m.group, m.venue, m.status, m.home_score, m.away_score, m.matchday)
        updated = db.recalculate_all()
        db.audit_log(g.user["id"], "SYNC_RESULTS", f"matches={len(matches)} bets_recalc={updated}")
        flash(f"Resultados sincronizados. {updated} apuestas recalculadas.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_sync"))


@app.route("/admin/equipos/agregar", methods=["POST"])
@admin_required
def add_team():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()
    group = request.form.get("group_name", "").strip().upper()
    flag = request.form.get("flag_url", "").strip()
    if not name:
        flash("Nombre obligatorio.", "error")
        return redirect(url_for("admin_sync"))
    db.upsert_team(name=name, code=code, flag_url=flag, group_name=group)
    db.audit_log(g.user["id"], "ADD_TEAM", name)
    flash(f"Equipo {name} agregado.", "success")
    return redirect(url_for("admin_sync"))


@app.route("/admin/resultados")
@admin_required
def admin_results():
    matches = db.get_all_matches()
    teams = db.get_all_teams()
    return render_template("admin/manual_results.html", matches=matches, teams=teams)


@app.route("/admin/resultados/<int:mid>", methods=["POST"])
@admin_required
def update_result(mid):
    hs = request.form.get("home_score", "").strip()
    aws = request.form.get("away_score", "").strip()
    status = request.form.get("status", "FINISHED")
    if hs != "" and aws != "":
        try:
            db.update_match_result(mid, int(hs), int(aws), status)
            # Recalculate bets for this match
            db.recalculate_all()
            db.audit_log(g.user["id"], "UPDATE_RESULT", f"match={mid} {hs}-{aws}")
            flash("Resultado actualizado.", "success")
        except ValueError:
            flash("Marcadores deben ser números.", "error")
    return redirect(url_for("admin_results"))


@app.route("/admin/partidos/agregar", methods=["POST"])
@admin_required
def add_match():
    ht = request.form.get("home_team_id", type=int)
    at = request.form.get("away_team_id", type=int)
    md = request.form.get("match_date", "")
    stage = request.form.get("stage", "GROUP_STAGE")
    grp = request.form.get("group_name", "").strip()
    venue = request.form.get("venue", "").strip()
    if not ht or not at or not md:
        flash("Completa todos los campos.", "error")
        return redirect(url_for("admin_results"))
    db.create_match(ht, at, md, stage, grp or None, venue or None)
    db.audit_log(g.user["id"], "ADD_MATCH", f"{ht} vs {at}")
    flash("Partido agregado.", "success")
    return redirect(url_for("admin_results"))


@app.route("/admin/recalcular", methods=["POST"])
@admin_required
def recalculate():
    ub = db.recalculate_all()
    us = db.recalculate_specials()
    db.audit_log(g.user["id"], "RECALCULATE", f"bets={ub} specials={us}")
    flash(f"Recálculo: {ub} apuestas, {us} especiales.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/configuracion", methods=["GET", "POST"])
@admin_required
def admin_config():
    teams = db.get_all_teams()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "set_lock_date":
            ld = request.form.get("lock_date", "")
            if ld:
                db.set_config("special_predictions_lock", ld)
                flash("Fecha actualizada.", "success")
        elif action == "set_actual_results":
            ci = request.form.get("champion_team_id", "")
            ri = request.form.get("runner_up_team_id", "")
            ts = request.form.get("top_scorer_name", "").strip()
            if ci: db.set_config("actual_champion_team_id", ci)
            if ri: db.set_config("actual_runner_up_team_id", ri)
            if ts: db.set_config("actual_top_scorer_name", ts)
            u = db.recalculate_specials()
            db.audit_log(g.user["id"], "SET_RESULTS", f"champ={ci} runner={ri} scorer={ts}")
            flash(f"Resultados cargados. {u} predicciones recalculadas.", "success")
        return redirect(url_for("admin_config"))
    
    cfg = {
        "lock_date": db.get_config("special_predictions_lock", app.config["SPECIAL_PREDICTIONS_LOCK"]),
        "champion_id": db.get_config("actual_champion_team_id", ""),
        "runner_up_id": db.get_config("actual_runner_up_team_id", ""),
        "top_scorer": db.get_config("actual_top_scorer_name", ""),
    }
    return render_template("admin/config.html", teams=teams, current_config=cfg)


# ═══════════════════════════════════════════════════════════════════════════════
# Startup
# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    db.init_db()
    db.ensure_admin(
        app.config["ADMIN_USERNAME"],
        app.config["ADMIN_PASSWORD"],
        app.config["ADMIN_DISPLAY_NAME"],
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"\n🏆 Mundial 2026 corriendo en http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
