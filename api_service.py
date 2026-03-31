"""
Capa de abstracción para APIs de fútbol.

Proveedores:
  1. OpenFootball (GitHub) — GRATIS, sin API key, datos del Mundial 2026
  2. football-data.org — requiere API key gratuita
  3. Manual — sin API, todo manual desde admin

OpenFootball es la opción recomendada: sin key, sin límites, datos actualizados.
"""
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NormalizedTeam:
    def __init__(self, api_id, name, code=None, flag_url=None, group=None):
        self.api_id = str(api_id)
        self.name = name
        self.code = code
        self.flag_url = flag_url
        self.group = group


class NormalizedMatch:
    def __init__(self, api_id, home_team_api_id, away_team_api_id, match_date,
                 stage=None, group=None, venue=None, status="SCHEDULED",
                 home_score=None, away_score=None, matchday=None):
        self.api_id = str(api_id)
        self.home_team_api_id = str(home_team_api_id) if home_team_api_id else None
        self.away_team_api_id = str(away_team_api_id) if away_team_api_id else None
        self.match_date = match_date
        self.stage = stage
        self.group = group
        self.venue = venue
        self.status = status
        self.home_score = home_score
        self.away_score = away_score
        self.matchday = matchday


# ─── OpenFootball Provider (GitHub JSON — GRATIS) ────────────────────────────

class OpenFootballProvider:
    """
    Fuente: https://github.com/openfootball/worldcup.json
    JSON público sin API key. Datos del Mundial 2026.
    """
    RESULTS_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

    def _fetch_json(self):
        import requests
        resp = requests.get(self.RESULTS_URL, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def fetch_teams(self, _=None):
        """OpenFootball no tiene endpoint de equipos, retorna vacío."""
        return []

    def fetch_matches(self, _=None):
        return self._parse_matches()

    def fetch_match_results(self, _=None):
        return self._parse_matches()

    def _parse_matches(self):
        data = self._fetch_json()
        matches = []
        for i, m in enumerate(data.get("matches", [])):
            date_str = m.get("date", "")
            time_str = m.get("time", "12:00")
            # Parsear fecha y hora
            try:
                # Formato: "2026-06-11" + "13:00 UTC-6"
                time_clean = time_str.split(" ")[0]  # "13:00"
                dt = datetime.fromisoformat(f"{date_str}T{time_clean}:00+00:00")
            except Exception:
                try:
                    dt = datetime.fromisoformat(date_str + "T18:00:00+00:00")
                except Exception:
                    continue

            # Score
            score = m.get("score", {})
            ft = score.get("ft", [None, None]) if score else [None, None]
            home_score = ft[0] if ft and len(ft) >= 2 else None
            away_score = ft[1] if ft and len(ft) >= 2 else None
            has_score = home_score is not None

            # Stage
            round_name = m.get("round", "")
            if "Matchday" in round_name:
                stage = "GROUP_STAGE"
            elif "Round of 32" in round_name:
                stage = "ROUND_OF_32"
            elif "Round of 16" in round_name:
                stage = "ROUND_OF_16"
            elif "Quarter" in round_name:
                stage = "QUARTER_FINALS"
            elif "Semi" in round_name:
                stage = "SEMI_FINALS"
            elif "Third" in round_name:
                stage = "THIRD_PLACE"
            elif "Final" in round_name:
                stage = "FINAL"
            else:
                stage = round_name

            # Group
            group = m.get("group", "")
            if group:
                group = group.replace("Group ", "")

            status = "FINISHED" if has_score else "SCHEDULED"

            matches.append(NormalizedMatch(
                api_id=f"of-{i}",
                home_team_api_id=m.get("team1", ""),
                away_team_api_id=m.get("team2", ""),
                match_date=dt, stage=stage, group=group or None,
                venue=m.get("ground", ""),
                status=status,
                home_score=home_score, away_score=away_score,
                matchday=None,
            ))
        return matches


# ─── football-data.org Provider ──────────────────────────────────────────────

class FootballDataProvider:
    """football-data.org v4. Free tier: 10 req/min."""
    def __init__(self, api_key, base_url="https://api.football-data.org/v4"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-Auth-Token": api_key}

    def _get(self, endpoint):
        import requests
        resp = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def fetch_teams(self, competition_id="WC"):
        data = self._get(f"/competitions/{competition_id}/teams")
        teams = []
        for t in data.get("teams", []):
            group = t.get("group", "")
            if group:
                group = group.replace("GROUP_", "")
            teams.append(NormalizedTeam(
                api_id=t["id"], name=t.get("shortName") or t.get("name", ""),
                code=t.get("tla", ""), flag_url=t.get("crest", ""), group=group or None,
            ))
        return teams

    def fetch_matches(self, competition_id="WC"):
        data = self._get(f"/competitions/{competition_id}/matches")
        return self._parse(data)

    def fetch_match_results(self, competition_id="WC"):
        return self.fetch_matches(competition_id)

    def _parse(self, data):
        matches = []
        for m in data.get("matches", []):
            try:
                md = datetime.fromisoformat(m.get("utcDate", "").replace("Z", "+00:00"))
            except Exception:
                md = datetime.now(timezone.utc)
            ft = m.get("score", {}).get("fullTime", {})
            group = m.get("group", "")
            if group:
                group = group.replace("GROUP_", "")
            matches.append(NormalizedMatch(
                api_id=m["id"],
                home_team_api_id=m.get("homeTeam", {}).get("id"),
                away_team_api_id=m.get("awayTeam", {}).get("id"),
                match_date=md, stage=m.get("stage", ""), group=group or None,
                venue=m.get("venue", ""), status=m.get("status", "SCHEDULED"),
                home_score=ft.get("home"), away_score=ft.get("away"),
                matchday=m.get("matchday"),
            ))
        return matches


# ─── Manual Provider ─────────────────────────────────────────────────────────

class ManualProvider:
    """Fallback sin API."""
    def fetch_teams(self, _=None): return []
    def fetch_matches(self, _=None): return []
    def fetch_match_results(self, _=None): return []


# ─── Factory ─────────────────────────────────────────────────────────────────

def get_provider(config):
    provider_name = config.get("FOOTBALL_API_PROVIDER", "openfootball")
    key = config.get("FOOTBALL_API_KEY", "")

    if provider_name == "openfootball":
        return OpenFootballProvider()

    if provider_name == "football-data" and key:
        return FootballDataProvider(key)

    # Default: openfootball (no requiere key)
    return OpenFootballProvider()
