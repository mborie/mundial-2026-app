"""
Seed: UEFA Champions League 2025/26 — Datos reales.
Incluye octavos (finalizados), cuartos (próximos), semis y final.
Ejecutar: python seed_champions.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SECRET_KEY", "seed-key")

from app import app
import database as db

# ═══════════════════════════════════════════════════════════════════════════════
# Equipos (los 8 clasificados a cuartos de final)
# ═══════════════════════════════════════════════════════════════════════════════

TEAMS = [
    # (nombre, código, grupo=None para knockout, flag_url)
    ("Arsenal",          "ARS", None, "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg"),
    ("Bayern München",   "BAY", None, "https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg"),
    ("Liverpool",        "LIV", None, "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg"),
    ("Barcelona",        "BAR", None, "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg"),
    ("Real Madrid",      "RMA", None, "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg"),
    ("Atlético Madrid",  "ATM", None, "https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_Madrid_2017_logo.svg"),
    ("PSG",              "PSG", None, "https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg"),
    ("Sporting CP",      "SCP", None, "https://upload.wikimedia.org/wikipedia/en/e/e1/Sporting_Clube_de_Portugal_%28Logo%29.svg"),
    # Equipos eliminados en octavos (para historial)
    ("Chelsea",          "CHE", None, "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg"),
    ("Galatasaray",      "GAL", None, "https://upload.wikimedia.org/wikipedia/commons/f/f6/Galatasaray_Sports_Club_Logo.svg"),
    ("Manchester City",  "MCI", None, "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg"),
    ("Atalanta",         "ATA", None, "https://upload.wikimedia.org/wikipedia/en/6/66/AtalantaBC.svg"),
    ("Newcastle United", "NEW", None, "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg"),
    ("Tottenham",        "TOT", None, "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg"),
    ("Bodø/Glimt",       "BOD", None, "https://upload.wikimedia.org/wikipedia/en/f/f7/FK_Bod%C3%B8-Glimt_logo.svg"),
    ("Leverkusen",       "LEV", None, "https://upload.wikimedia.org/wikipedia/en/5/59/Bayer_04_Leverkusen_logo.svg"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# Partidos - Todos los horarios en UTC (21:00 CET/CEST = 19:00 UTC)
# ═══════════════════════════════════════════════════════════════════════════════

# Formato: (local_code, visita_code, fecha_utc, fase, sede, status, score_local, score_visita, matchday)

MATCHES = [
    # ─── OCTAVOS DE FINAL — IDA (10-11 Marzo) — FINALIZADOS ───────────────
    ("PSG",  "CHE", "2026-03-10T20:00:00", "ROUND_OF_16", "Parc des Princes",    "FINISHED", 4, 1, 1),
    ("GAL",  "LIV", "2026-03-10T20:00:00", "ROUND_OF_16", "Rams Park",           "FINISHED", 2, 1, 1),
    ("RMA",  "MCI", "2026-03-11T20:00:00", "ROUND_OF_16", "Santiago Bernabéu",   "FINISHED", 3, 0, 1),
    ("ATA",  "BAY", "2026-03-11T20:00:00", "ROUND_OF_16", "Gewiss Stadium",      "FINISHED", 0, 5, 1),
    ("NEW",  "BAR", "2026-03-10T20:00:00", "ROUND_OF_16", "St James' Park",      "FINISHED", 2, 4, 1),
    ("ATM",  "TOT", "2026-03-10T20:00:00", "ROUND_OF_16", "Metropolitano",       "FINISHED", 4, 3, 1),
    ("BOD",  "SCP", "2026-03-11T20:00:00", "ROUND_OF_16", "Aspmyra Stadion",     "FINISHED", 2, 3, 1),
    ("LEV",  "ARS", "2026-03-11T20:00:00", "ROUND_OF_16", "BayArena",            "FINISHED", 0, 1, 1),

    # ─── OCTAVOS DE FINAL — VUELTA (17-18 Marzo) — FINALIZADOS ────────────
    ("CHE",  "PSG", "2026-03-17T20:00:00", "ROUND_OF_16", "Stamford Bridge",     "FINISHED", 1, 4, 2),
    ("LIV",  "GAL", "2026-03-17T20:00:00", "ROUND_OF_16", "Anfield",             "FINISHED", 3, 0, 2),
    ("MCI",  "RMA", "2026-03-18T20:00:00", "ROUND_OF_16", "Etihad Stadium",      "FINISHED", 1, 2, 2),
    ("BAY",  "ATA", "2026-03-18T20:00:00", "ROUND_OF_16", "Allianz Arena",       "FINISHED", 5, 2, 2),
    ("BAR",  "NEW", "2026-03-17T20:00:00", "ROUND_OF_16", "Camp Nou",            "FINISHED", 4, 1, 2),
    ("TOT",  "ATM", "2026-03-17T20:00:00", "ROUND_OF_16", "Tottenham Stadium",   "FINISHED", 2, 3, 2),
    ("SCP",  "BOD", "2026-03-18T20:00:00", "ROUND_OF_16", "José Alvalade",       "FINISHED", 2, 1, 2),
    ("ARS",  "LEV", "2026-03-18T20:00:00", "ROUND_OF_16", "Emirates Stadium",    "FINISHED", 2, 1, 2),

    # ─── CUARTOS DE FINAL — IDA (7-8 Abril) — PRÓXIMOS ────────────────────
    ("SCP",  "ARS", "2026-04-07T19:00:00", "QUARTER_FINALS", "José Alvalade",    "SCHEDULED", None, None, 1),
    ("RMA",  "BAY", "2026-04-07T19:00:00", "QUARTER_FINALS", "Santiago Bernabéu", "SCHEDULED", None, None, 1),
    ("BAR",  "ATM", "2026-04-08T19:00:00", "QUARTER_FINALS", "Camp Nou",         "SCHEDULED", None, None, 1),
    ("PSG",  "LIV", "2026-04-08T19:00:00", "QUARTER_FINALS", "Parc des Princes", "SCHEDULED", None, None, 1),

    # ─── CUARTOS DE FINAL — VUELTA (14-15 Abril) ──────────────────────────
    ("ATM",  "BAR", "2026-04-14T19:00:00", "QUARTER_FINALS", "Metropolitano",    "SCHEDULED", None, None, 2),
    ("LIV",  "PSG", "2026-04-14T19:00:00", "QUARTER_FINALS", "Anfield",          "SCHEDULED", None, None, 2),
    ("ARS",  "SCP", "2026-04-15T19:00:00", "QUARTER_FINALS", "Emirates Stadium", "SCHEDULED", None, None, 2),
    ("BAY",  "RMA", "2026-04-15T19:00:00", "QUARTER_FINALS", "Allianz Arena",    "SCHEDULED", None, None, 2),

    # ─── SEMIFINALES — IDA (28-29 Abril) ───────────────────────────────────
    # (TBD: ganadores de cuartos)
    # Semi 1: Ganador PSG/LIV vs Ganador RMA/BAY
    # Semi 2: Ganador BAR/ATM vs Ganador SCP/ARS

    # ─── FINAL — 30 Mayo — Puskás Aréna, Budapest ─────────────────────────
]

# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    print("\n⚽ Champions League 2025/26 — Cargando datos reales\n")

    # Reset DB
    db.init_db()
    conn = db.get_db()
    conn.execute("DELETE FROM bets")
    conn.execute("DELETE FROM special_predictions")
    conn.execute("DELETE FROM matches")
    conn.execute("DELETE FROM teams")
    conn.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()

    # Teams
    team_ids = {}
    for name, code, group, flag in TEAMS:
        tid, _ = db.upsert_team(name=name, code=code, flag_url=flag, group_name=group)
        team_ids[code] = tid
    print(f"  ✓ {len(TEAMS)} equipos cargados")

    # Matches
    mc = 0
    for home_c, away_c, dt, stage, venue, status, hs, aws, md in MATCHES:
        ht = team_ids.get(home_c)
        at = team_ids.get(away_c)
        if not ht or not at:
            print(f"  ⚠ Equipo no encontrado: {home_c} o {away_c}")
            continue

        conn = db.get_db()
        is_final = 1 if status == "FINISHED" else 0
        conn.execute("""INSERT INTO matches
            (home_team_id, away_team_id, match_date, stage, group_name, venue, status,
             home_score, away_score, is_result_final, matchday)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (ht, at, dt, stage, None, venue, status, hs, aws, is_final, md))
        conn.commit()
        conn.close()
        mc += 1
    print(f"  ✓ {mc} partidos cargados")

    # Usuarios de prueba
    for uname, dname, pw, approved in [
        ("jperez",   "Juan Pérez",    "123456", 1),
        ("mgarcia",  "María García",  "123456", 1),
        ("clopez",   "Carlos López",  "123456", 1),
        ("amorales", "Ana Morales",   "123456", 1),
        ("rsoto",    "Roberto Soto",  "123456", 1),
    ]:
        db.create_user(uname, dname, pw, is_approved=approved)
    print("  ✓ 5 usuarios de prueba (todos aprobados)")

    # Simular apuestas en octavos (para que el ranking tenga datos)
    import random
    random.seed(42)

    conn = db.get_db()
    finished_matches = conn.execute(
        "SELECT id, home_score, away_score FROM matches WHERE is_result_final=1"
    ).fetchall()
    users = conn.execute("SELECT id FROM users WHERE role='user'").fetchall()
    conn.close()

    bets_count = 0
    for m in finished_matches:
        result = db.get_match_result_code(m["home_score"], m["away_score"])
        for u in users:
            # Cada usuario tiene ~40% de acertar
            choices = ["1", "X", "2"]
            if random.random() < 0.4:
                pred = result  # acertará
            else:
                pred = random.choice([c for c in choices if c != result] or choices)
            db.place_bet(u["id"], m["id"], pred)
            bets_count += 1

    print(f"  ✓ {bets_count} apuestas simuladas en octavos")

    # Recalcular puntos
    updated = db.recalculate_all()
    print(f"  ✓ {updated} apuestas puntuadas")

    # Config
    db.set_config("special_predictions_lock", "2026-04-07T19:00:00+00:00")

    # Simular predicciones especiales para algunos
    for uid_offset, champ, runner, scorer in [
        (0, "RMA", "BAR", "Kylian Mbappé"),
        (1, "BAY", "ARS", "Harry Kane"),
        (2, "LIV", "RMA", "Mohamed Salah"),
        (3, "BAR", "PSG", "Robert Lewandowski"),
        (4, "ARS", "BAY", "Bukayo Saka"),
    ]:
        uid = users[uid_offset]["id"]
        db.save_special_prediction(uid, team_ids.get(champ), team_ids.get(runner), scorer)

    print("  ✓ Pronósticos especiales simulados")

    # Mostrar ranking
    ranking = db.get_ranking()
    print(f"\n  📊 Ranking actual:")
    for r in ranking:
        print(f"     #{r['position']} {r['display_name']:15} — {r['total_points']} pts ({r['correct_bets']}/{r['total_bets']} aciertos)")

    print(f"""
  ════════════════════════════════════════════════
  ✅ Seed completado!

  Admin:    admin / admin2026!
  Usuarios: jperez, mgarcia, clopez, amorales, rsoto / 123456

  📅 Próximos partidos:
     7 Abr — Sporting CP vs Arsenal (19:00 UTC)
     7 Abr — Real Madrid vs Bayern München (19:00 UTC)
     8 Abr — Barcelona vs Atlético Madrid (19:00 UTC)
     8 Abr — PSG vs Liverpool (19:00 UTC)
    14 Abr — Atlético Madrid vs Barcelona (19:00 UTC)
    14 Abr — Liverpool vs PSG (19:00 UTC)
    15 Abr — Arsenal vs Sporting CP (19:00 UTC)
    15 Abr — Bayern München vs Real Madrid (19:00 UTC)

  16 partidos de octavos ya finalizados con resultados reales.
  Apuestas simuladas para que el ranking funcione.
  ════════════════════════════════════════════════
""")
