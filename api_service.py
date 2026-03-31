"""
Capa de abstracción para APIs de fútbol.
"""
import logging
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


class FootballDataProvider:
    """football-data.org v4. Free tier: 10 req/min."""
    def __init__(self, api_key, base_url="https://api.football-data.org/v4"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-Auth-Token": api_key}
    
    def _get(self, endpoint):
        import requests
        resp = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=15)
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


class ManualProvider:
    """Fallback sin API."""
    def fetch_teams(self, _=None): return []
    def fetch_matches(self, _=None): return []
    def fetch_match_results(self, _=None): return []


def get_provider(config):
    key = config.get("FOOTBALL_API_KEY", "")
    if key:
        return FootballDataProvider(key)
    return ManualProvider()
