"""
🏆 Seed: FIFA World Cup 2026 — Datos reales de producción.
NO datos de prueba. NO usuarios ficticios. NO apuestas simuladas.

Incluye:
  - 48 equipos (42 clasificados + 6 pendientes de playoffs)
  - 6 partidos de playoffs (UEFA + Intercontinental) — HOY 31 Marzo
  - 72 partidos de fase de grupos (11 Jun - 27 Jun)
  - Sin usuarios de prueba (solo admin)

Ejecutar: python seed_worldcup.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SECRET_KEY", "seed-key")

from app import app
import database as db

# ═══════════════════════════════════════════════════════════════════════════════
# 48 EQUIPOS — Fuente: FIFA.com sorteo 5 Dic 2025
# Flag URLs from flagcdn.com (ISO 3166-1 alpha-2)
# ═══════════════════════════════════════════════════════════════════════════════

F = "https://flagcdn.com/w80"  # base URL

TEAMS = [
    # GRUPO A
    ("México",          "MEX", "A", f"{F}/mx.png"),
    ("Corea del Sur",   "KOR", "A", f"{F}/kr.png"),
    ("Sudáfrica",       "RSA", "A", f"{F}/za.png"),
    # Playoff D → se actualiza al conocer ganador
    ("Ganador Playoff D","PLD", "A", f"{F}/eu.png"),

    # GRUPO B
    ("Canadá",          "CAN", "B", f"{F}/ca.png"),
    ("Suiza",           "SUI", "B", f"{F}/ch.png"),
    ("Qatar",           "QAT", "B", f"{F}/qa.png"),
    ("Ganador Playoff A","PLA", "B", f"{F}/eu.png"),

    # GRUPO C
    ("Brasil",          "BRA", "C", f"{F}/br.png"),
    ("Marruecos",       "MAR", "C", f"{F}/ma.png"),
    ("Escocia",         "SCO", "C", f"{F}/gb-sct.png"),
    ("Haití",           "HAI", "C", f"{F}/ht.png"),

    # GRUPO D
    ("Estados Unidos",  "USA", "D", f"{F}/us.png"),
    ("Australia",       "AUS", "D", f"{F}/au.png"),
    ("Paraguay",        "PAR", "D", f"{F}/py.png"),
    ("Ganador Playoff C","PLC", "D", f"{F}/eu.png"),

    # GRUPO E
    ("Alemania",        "GER", "E", f"{F}/de.png"),
    ("Ecuador",         "ECU", "E", f"{F}/ec.png"),
    ("Costa de Marfil", "CIV", "E", f"{F}/ci.png"),
    ("Curaçao",         "CUR", "E", f"{F}/cw.png"),

    # GRUPO F
    ("Japón",           "JPN", "F", f"{F}/jp.png"),
    ("Países Bajos",    "NED", "F", f"{F}/nl.png"),
    ("Túnez",           "TUN", "F", f"{F}/tn.png"),
    ("Ganador Playoff B","PLB", "F", f"{F}/eu.png"),

    # GRUPO G
    ("Bélgica",         "BEL", "G", f"{F}/be.png"),
    ("Irán",            "IRN", "G", f"{F}/ir.png"),
    ("Egipto",          "EGY", "G", f"{F}/eg.png"),
    ("Nueva Zelanda",   "NZL", "G", f"{F}/nz.png"),

    # GRUPO H
    ("España",          "ESP", "H", f"{F}/es.png"),
    ("Uruguay",         "URU", "H", f"{F}/uy.png"),
    ("Arabia Saudita",  "KSA", "H", f"{F}/sa.png"),
    ("Cabo Verde",      "CPV", "H", f"{F}/cv.png"),

    # GRUPO I
    ("Francia",         "FRA", "I", f"{F}/fr.png"),
    ("Senegal",         "SEN", "I", f"{F}/sn.png"),
    ("Noruega",         "NOR", "I", f"{F}/no.png"),
    ("Ganador Interconf 2","IC2","I", f"{F}/un.png"),

    # GRUPO J
    ("Argentina",       "ARG", "J", f"{F}/ar.png"),
    ("Austria",         "AUT", "J", f"{F}/at.png"),
    ("Argelia",         "ALG", "J", f"{F}/dz.png"),
    ("Jordania",        "JOR", "J", f"{F}/jo.png"),

    # GRUPO K
    ("Portugal",        "POR", "K", f"{F}/pt.png"),
    ("Colombia",        "COL", "K", f"{F}/co.png"),
    ("Uzbekistán",      "UZB", "K", f"{F}/uz.png"),
    ("Ganador Interconf 1","IC1","K", f"{F}/un.png"),

    # GRUPO L
    ("Inglaterra",      "ENG", "L", f"{F}/gb-eng.png"),
    ("Croacia",         "CRO", "L", f"{F}/hr.png"),
    ("Ghana",           "GHA", "L", f"{F}/gh.png"),
    ("Panamá",          "PAN", "L", f"{F}/pa.png"),

    # ── Equipos en playoffs (para partidos de hoy) ──
    ("Italia",                  "ITA", None, f"{F}/it.png"),
    ("Bosnia y Herzegovina",    "BIH", None, f"{F}/ba.png"),
    ("Suecia",                  "SWE", None, f"{F}/se.png"),
    ("Polonia",                 "POL", None, f"{F}/pl.png"),
    ("Turquía",                 "TUR", None, f"{F}/tr.png"),
    ("Kosovo",                  "KOS", None, f"{F}/xk.png"),
    ("Dinamarca",               "DEN", None, f"{F}/dk.png"),
    ("Chequia",                 "CZE", None, f"{F}/cz.png"),
    ("RD Congo",                "COD", None, f"{F}/cd.png"),
    ("Jamaica",                 "JAM", None, f"{F}/jm.png"),
    ("Irak",                    "IRQ", None, f"{F}/iq.png"),
    ("Bolivia",                 "BOL", None, f"{F}/bo.png"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# PLAYOFFS — 31 MARZO 2026 (HOY)
# Horarios en UTC. UEFA: 18:45 UTC (20:45 CET). Interconf: en México.
# ═══════════════════════════════════════════════════════════════════════════════

PLAYOFFS = [
    # UEFA Playoff Finals - 31 Marzo 2026
    ("BIH","ITA", "2026-03-31T18:45:00", "PLAYOFF", None, "Bilino Polje, Zenica",         "SCHEDULED"),
    ("SWE","POL", "2026-03-31T18:45:00", "PLAYOFF", None, "Friends Arena, Estocolmo",      "SCHEDULED"),
    ("KOS","TUR", "2026-03-31T18:45:00", "PLAYOFF", None, "Fadil Vokrri, Pristina",        "SCHEDULED"),
    ("CZE","DEN", "2026-03-31T18:45:00", "PLAYOFF", None, "Eden Arena, Praga",             "SCHEDULED"),
    # Intercontinental Playoff Finals - 31 Marzo 2026
    ("COD","JAM", "2026-03-31T23:00:00", "PLAYOFF", None, "Estadio Akron, Guadalajara",    "SCHEDULED"),
    ("IRQ","BOL", "2026-04-01T01:00:00", "PLAYOFF", None, "Estadio BBVA, Monterrey",       "SCHEDULED"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# FASE DE GRUPOS — 72 partidos (11 Jun - 27 Jun 2026)
# Horarios UTC. Fuente: FIFA match schedule / Bleacher Report / MLS Soccer
# Formato: (local, visita, fecha_utc, grupo, sede)
# ═══════════════════════════════════════════════════════════════════════════════

GROUP_MATCHES = [
    # ── JORNADA 1 (11-16 Jun) ─────────────────────────────────────────────
    # 11 Jun
    ("MEX","RSA", "2026-06-11T19:00:00", "A", "Estadio Azteca, CDMX"),
    ("KOR","PLD", "2026-06-11T22:00:00", "A", "Estadio BBVA, Monterrey"),
    # 12 Jun
    ("BRA","MAR", "2026-06-12T17:00:00", "C", "BMO Field, Toronto"),
    ("PLA","QAT", "2026-06-12T19:00:00", "B", "SoFi Stadium, Los Angeles"),
    ("CAN","SUI", "2026-06-12T22:00:00", "B", "BC Place, Vancouver"),
    ("USA","PAR", "2026-06-12T20:00:00", "D", "SoFi Stadium, Los Angeles"),
    ("SCO","HAI", "2026-06-12T23:00:00", "C", "Gillette Stadium, Boston"),
    # 13 Jun
    ("GER","CUR", "2026-06-13T17:00:00", "E", "Estadio Akron, Guadalajara"),
    ("JPN","NED", "2026-06-13T17:00:00", "F", "Mercedes-Benz, Atlanta"),
    ("ARG","ALG", "2026-06-14T01:00:00", "J", "Arrowhead Stadium, Kansas City"),
    ("AUT","JOR", "2026-06-13T23:00:00", "J", "Levi's Stadium, San Francisco"),
    ("ESP","CPV", "2026-06-13T20:00:00", "H", "Hard Rock Stadium, Miami"),
    ("BEL","EGY", "2026-06-13T23:00:00", "G", "MetLife Stadium, Nueva Jersey"),
    # 14 Jun
    ("CIV","ECU", "2026-06-14T17:00:00", "E", "Gillette Stadium, Boston"),
    ("PLB","TUN", "2026-06-14T20:00:00", "F", "Mercedes-Benz, Atlanta"),
    ("KSA","URU", "2026-06-14T22:00:00", "H", "Hard Rock Stadium, Miami"),
    ("IRN","NZL", "2026-06-15T01:00:00", "G", "SoFi Stadium, Los Angeles"),
    ("PLC","AUS", "2026-06-14T17:00:00", "D", "Levi's Stadium, San Francisco"),
    # 15 Jun
    ("FRA","SEN", "2026-06-15T19:00:00", "I", "MetLife Stadium, Nueva Jersey"),
    ("IC2","NOR", "2026-06-15T22:00:00", "I", "Gillette Stadium, Boston"),
    # 16 Jun
    ("POR","IC1", "2026-06-16T17:00:00", "K", "NRG Stadium, Houston"),
    ("UZB","COL", "2026-06-16T20:00:00", "K", "Estadio Azteca, CDMX"),
    ("ENG","CRO", "2026-06-16T20:00:00", "L", "AT&T Stadium, Dallas"),
    ("GHA","PAN", "2026-06-16T23:00:00", "L", "BMO Field, Toronto"),

    # ── JORNADA 2 (17-22 Jun) ─────────────────────────────────────────────
    # 17 Jun
    ("JPN","TUN", "2026-06-17T17:00:00", "F", "Mercedes-Benz, Atlanta"),
    ("POR","UZB", "2026-06-17T20:00:00", "K", "NRG Stadium, Houston"),
    # 18 Jun
    ("PLD","RSA", "2026-06-18T16:00:00", "A", "Mercedes-Benz, Atlanta"),
    ("SUI","PLA", "2026-06-18T19:00:00", "B", "SoFi Stadium, Los Angeles"),
    ("MEX","KOR", "2026-06-19T01:00:00", "A", "Estadio Akron, Guadalajara"),
    ("USA","AUS", "2026-06-18T22:00:00", "D", "Lumen Field, Seattle"),
    # 19 Jun
    ("BRA","HAI", "2026-06-19T17:00:00", "C", "AT&T Stadium, Dallas"),
    ("SCO","MAR", "2026-06-19T22:00:00", "C", "Gillette Stadium, Boston"),
    # 20 Jun
    ("NED","PLB", "2026-06-20T17:00:00", "F", "NRG Stadium, Houston"),
    ("GER","CIV", "2026-06-20T20:00:00", "E", "Gillette Stadium, Boston"),
    # 21 Jun
    ("ESP","KSA", "2026-06-21T17:00:00", "H", "Estadio Akron, Guadalajara"),
    ("URU","CPV", "2026-06-21T17:00:00", "H", "Hard Rock Stadium, Miami"),
    ("BEL","IRN", "2026-06-21T20:00:00", "G", "SoFi Stadium, Los Angeles"),
    ("EGY","NZL", "2026-06-21T20:00:00", "G", "MetLife Stadium, Nueva Jersey"),
    ("CAN","QAT", "2026-06-21T23:00:00", "B", "BMO Field, Toronto"),
    ("CUR","CIV", "2026-06-21T23:00:00", "E", "NRG Stadium, Houston"),
    # 22 Jun
    ("FRA","NOR", "2026-06-22T17:00:00", "I", "MetLife Stadium, Nueva Jersey"),
    ("SEN","IC2", "2026-06-22T20:00:00", "I", "Gillette Stadium, Boston"),
    ("COL","IC1", "2026-06-23T02:00:00", "K", "Estadio Azteca, CDMX"),
    # 23 Jun
    ("ENG","GHA", "2026-06-23T17:00:00", "L", "Gillette Stadium, Boston"),
    ("PAR","PLC", "2026-06-23T17:00:00", "D", "Levi's Stadium, San Francisco"),
    ("ARG","AUT", "2026-06-23T20:00:00", "J", "Arrowhead Stadium, Kansas City"),
    ("JOR","ALG", "2026-06-23T20:00:00", "J", "AT&T Stadium, Dallas"),
    ("PAN","CRO", "2026-06-23T23:00:00", "L", "BMO Field, Toronto"),
    ("USA","PLC", "2026-06-24T04:00:00", "D", "SoFi Stadium, Los Angeles"),

    # ── JORNADA 3 (24-27 Jun) — Partidos simultáneos por grupo ────────────
    # 24 Jun
    ("RSA","KOR", "2026-06-24T20:00:00", "A", "Mercedes-Benz, Atlanta"),
    ("PLD","MEX", "2026-06-25T02:00:00", "A", "Estadio Azteca, CDMX"),
    ("MAR","HAI", "2026-06-24T17:00:00", "C", "Hard Rock Stadium, Miami"),
    # 25 Jun
    ("ECU","CUR", "2026-06-25T17:00:00", "E", "NRG Stadium, Houston"),
    ("GER","ECU", "2026-06-25T20:00:00", "E", "MetLife Stadium, Nueva Jersey"),  # Note: simultáneo
    ("JPN","PLB", "2026-06-25T20:00:00", "F", "Mercedes-Benz, Atlanta"),
    ("TUN","NED", "2026-06-25T20:00:00", "F", "AT&T Stadium, Dallas"),
    ("AUS","PAR", "2026-06-25T23:00:00", "D", "Levi's Stadium, San Francisco"),
    # 26 Jun
    ("URU","ESP", "2026-06-26T17:00:00", "H", "Estadio Akron, Guadalajara"),
    ("CPV","KSA", "2026-06-26T17:00:00", "H", "Hard Rock Stadium, Miami"),
    ("BEL","NZL", "2026-06-26T20:00:00", "G", "MetLife Stadium, Nueva Jersey"),
    ("EGY","IRN", "2026-06-26T20:00:00", "G", "SoFi Stadium, Los Angeles"),
    ("SUI","QAT", "2026-06-26T23:00:00", "B", "BC Place, Vancouver"),
    ("CAN","PLA", "2026-06-26T23:00:00", "B", "BMO Field, Toronto"),
    ("BRA","SCO", "2026-06-27T02:00:00", "C", "AT&T Stadium, Dallas"),
    # 27 Jun
    ("FRA","IC2", "2026-06-27T17:00:00", "I", "Gillette Stadium, Boston"),
    ("NOR","SEN", "2026-06-27T17:00:00", "I", "MetLife Stadium, Nueva Jersey"),  # Note: check
    ("ARG","JOR", "2026-06-27T20:00:00", "J", "Arrowhead Stadium, Kansas City"),
    ("ALG","AUT", "2026-06-27T20:00:00", "J", "Levi's Stadium, San Francisco"),
    ("IC1","UZB", "2026-06-27T23:00:00", "K", "Estadio Azteca, CDMX"),
    ("COL","POR", "2026-06-27T23:00:00", "K", "NRG Stadium, Houston"),
    ("PAN","ENG", "2026-06-28T02:00:00", "L", "MetLife Stadium, Nueva Jersey"),
    ("CRO","GHA", "2026-06-28T02:00:00", "L", "AT&T Stadium, Dallas"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    print("\n🏆 FIFA World Cup 2026 — Cargando datos de producción\n")

    db.init_db()
    db.migrate_db()
    # Limpiar datos previos
    conn = db.get_db()
    for table in ["bets", "special_predictions", "matches", "teams", "audit_log", "competitions"]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()

    # ── Crear competición ──
    wc_id = db.create_competition("WORLD_CUP", "FIFA World Cup 2026", "Mundial", "2026", 1)
    print(f"  ✓ Competición creada: Mundial 2026 (id={wc_id})")

    # ── Equipos ──
    team_ids = {}
    for name, code, group, flag in TEAMS:
        tid, _ = db.upsert_team(name=name, code=code, flag_url=flag, group_name=group, competition_id=wc_id)
        team_ids[code] = tid
    print(f"  ✓ {len(TEAMS)} equipos cargados ({len([t for t in TEAMS if t[2]])} en grupos + {len([t for t in TEAMS if not t[2]])} en playoffs)")

    # ── Playoffs (HOY) ──
    pc = 0
    for hc, ac, dt, stage, group, venue, status in PLAYOFFS:
        ht, at = team_ids.get(hc), team_ids.get(ac)
        if ht and at:
            db.create_match(ht, at, dt, stage, group, venue, competition_id=wc_id)
            pc += 1
    print(f"  ✓ {pc} partidos de playoffs cargados (HOY 31 Marzo)")

    # ── Fase de Grupos ──
    gc = 0
    for hc, ac, dt, group, venue in GROUP_MATCHES:
        ht, at = team_ids.get(hc), team_ids.get(ac)
        if ht and at:
            db.create_match(ht, at, dt, "GROUP_STAGE", group, venue, competition_id=wc_id)
            gc += 1
        else:
            missing = hc if not team_ids.get(hc) else ac
            print(f"  ⚠ Equipo no encontrado: {missing}")
    print(f"  ✓ {gc} partidos de fase de grupos cargados (11 Jun - 28 Jun)")

    # ── Config ──
    # Cierre de especiales: antes del primer partido del Mundial
    db.set_config("special_predictions_lock", "2026-06-11T18:00:00+00:00")

    print(f"""
  ══════════════════════════════════════════════════════════════
  ✅ Datos de producción cargados exitosamente

  📊 Resumen:
     {len(TEAMS)} equipos
     {pc} partidos de playoffs (31 Marzo 2026)
     {gc} partidos fase de grupos (11 Jun - 28 Jun)
     {pc + gc} partidos TOTAL

  🔑 Admin: admin / admin2026!
     (Cambia la contraseña en .env antes de producción)

  📅 Partidos disponibles para apostar HOY:
     🏴 Bosnia vs Italia (Playoff A)
     🇸🇪 Suecia vs Polonia (Playoff B)
     🇽🇰 Kosovo vs Turquía (Playoff C)
     🇨🇿 Chequia vs Dinamarca (Playoff D)
     🇨🇩 RD Congo vs Jamaica (Interconf 1)
     🇮🇶 Irak vs Bolivia (Interconf 2)

  ⚙️ Próximos pasos:
     1. Registra tu API key en .env (football-data.org)
        o actualiza resultados manualmente en Admin → Resultados
     2. Comparte el link con tu equipo
     3. Cuando se conozcan los ganadores de playoffs,
        actualiza los nombres "Ganador Playoff X" desde Admin
  ══════════════════════════════════════════════════════════════
""")
