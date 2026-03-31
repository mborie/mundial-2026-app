"""
Seed de datos de ejemplo. Ejecutar: python seed.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("SECRET_KEY", "seed-key")
from app import app
import database as db

TEAMS = [
    ("Estados Unidos", "USA", "A", "https://flagcdn.com/w80/us.png"),
    ("México", "MEX", "A", "https://flagcdn.com/w80/mx.png"),
    ("Canadá", "CAN", "A", "https://flagcdn.com/w80/ca.png"),
    ("Colombia", "COL", "A", "https://flagcdn.com/w80/co.png"),
    ("Brasil", "BRA", "B", "https://flagcdn.com/w80/br.png"),
    ("Argentina", "ARG", "B", "https://flagcdn.com/w80/ar.png"),
    ("Uruguay", "URU", "B", "https://flagcdn.com/w80/uy.png"),
    ("Chile", "CHI", "B", "https://flagcdn.com/w80/cl.png"),
    ("Francia", "FRA", "C", "https://flagcdn.com/w80/fr.png"),
    ("Alemania", "GER", "C", "https://flagcdn.com/w80/de.png"),
    ("España", "ESP", "C", "https://flagcdn.com/w80/es.png"),
    ("Portugal", "POR", "C", "https://flagcdn.com/w80/pt.png"),
    ("Inglaterra", "ENG", "D", "https://flagcdn.com/w80/gb-eng.png"),
    ("Países Bajos", "NED", "D", "https://flagcdn.com/w80/nl.png"),
    ("Bélgica", "BEL", "D", "https://flagcdn.com/w80/be.png"),
    ("Dinamarca", "DEN", "D", "https://flagcdn.com/w80/dk.png"),
    ("Italia", "ITA", "E", "https://flagcdn.com/w80/it.png"),
    ("Croacia", "CRO", "E", "https://flagcdn.com/w80/hr.png"),
    ("Japón", "JPN", "E", "https://flagcdn.com/w80/jp.png"),
    ("Corea del Sur", "KOR", "E", "https://flagcdn.com/w80/kr.png"),
    ("Senegal", "SEN", "F", "https://flagcdn.com/w80/sn.png"),
    ("Marruecos", "MAR", "F", "https://flagcdn.com/w80/ma.png"),
    ("Ghana", "GHA", "F", "https://flagcdn.com/w80/gh.png"),
    ("Nigeria", "NGA", "F", "https://flagcdn.com/w80/ng.png"),
    ("Australia", "AUS", "G", "https://flagcdn.com/w80/au.png"),
    ("Arabia Saudita", "KSA", "G", "https://flagcdn.com/w80/sa.png"),
    ("Irán", "IRN", "G", "https://flagcdn.com/w80/ir.png"),
    ("Qatar", "QAT", "G", "https://flagcdn.com/w80/qa.png"),
    ("Suiza", "SUI", "H", "https://flagcdn.com/w80/ch.png"),
    ("Austria", "AUT", "H", "https://flagcdn.com/w80/at.png"),
    ("Serbia", "SRB", "H", "https://flagcdn.com/w80/rs.png"),
    ("Ecuador", "ECU", "H", "https://flagcdn.com/w80/ec.png"),
]

MATCHES = [
    ("USA","COL","2026-06-11T16:00:00","A",1), ("MEX","CAN","2026-06-11T19:00:00","A",1),
    ("BRA","CHI","2026-06-12T16:00:00","B",1), ("ARG","URU","2026-06-12T19:00:00","B",1),
    ("FRA","POR","2026-06-13T16:00:00","C",1), ("GER","ESP","2026-06-13T19:00:00","C",1),
    ("ENG","DEN","2026-06-14T16:00:00","D",1), ("NED","BEL","2026-06-14T19:00:00","D",1),
    ("ITA","KOR","2026-06-15T16:00:00","E",1), ("CRO","JPN","2026-06-15T19:00:00","E",1),
    ("SEN","NGA","2026-06-16T16:00:00","F",1), ("MAR","GHA","2026-06-16T19:00:00","F",1),
    ("AUS","QAT","2026-06-17T16:00:00","G",1), ("KSA","IRN","2026-06-17T19:00:00","G",1),
    ("SUI","ECU","2026-06-18T16:00:00","H",1), ("AUT","SRB","2026-06-18T19:00:00","H",1),
    ("USA","MEX","2026-06-21T16:00:00","A",2), ("CAN","COL","2026-06-21T19:00:00","A",2),
    ("BRA","ARG","2026-06-22T16:00:00","B",2), ("URU","CHI","2026-06-22T19:00:00","B",2),
    ("FRA","GER","2026-06-23T16:00:00","C",2), ("ESP","POR","2026-06-23T19:00:00","C",2),
    ("ENG","NED","2026-06-24T16:00:00","D",2), ("BEL","DEN","2026-06-24T19:00:00","D",2),
]

with app.app_context():
    print("\n🏆 Cargando datos de ejemplo\n")
    
    # Teams
    team_ids = {}
    for name, code, group, flag in TEAMS:
        tid, created = db.upsert_team(name=name, code=code, flag_url=flag, group_name=group)
        team_ids[code] = tid
    print(f"  ✓ {len(TEAMS)} equipos cargados")
    
    # Matches
    mc = 0
    for hc, ac, dt, grp, md in MATCHES:
        ht, at = team_ids.get(hc), team_ids.get(ac)
        if ht and at:
            db.create_match(ht, at, dt, "GROUP_STAGE", grp, "Estadio por confirmar", matchday=md)
            mc += 1
    print(f"  ✓ {mc} partidos creados")
    
    # Users
    for uname, dname, pw, approved in [
        ("jperez","Juan Pérez","123456",1), ("mgarcia","María García","123456",1),
        ("clopez","Carlos López","123456",1), ("amorales","Ana Morales","123456",0),
    ]:
        db.create_user(uname, dname, pw, is_approved=approved)
    print("  ✓ 4 usuarios de prueba creados")
    
    db.set_config("special_predictions_lock", "2026-06-11T16:00:00+00:00")
    print("  ✓ Configuración inicializada")
    
    print(f"\n  Admin: admin / admin2026!")
    print(f"  Usuarios: jperez, mgarcia, clopez / 123456")
    print(f"  Pendiente: amorales / 123456\n")
