from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Union, Any
import pyjq


@dataclass
class Tournament:
    id: str
    name: str
    country: str

@dataclass
class Team:
    id: int
    name: str
    score: int

@dataclass
class Match:
    id: int
    date: str
    timestamp: float
    status: Literal["inprogress", "finished"]
    tournament: Tournament
    awayTeam: Team
    homeTeam: Team

@dataclass
class MatchesByTournament:
    tournamentName: str
    matches: list[Match]





class Player:
    def __init__(self, id: int, name: str, jerseyNumber: str, substitute: bool=False, goals: int=0, ownGoals: int=0) -> None:
        self.id = id
        self.name = name
        self.substitute = substitute
        self.jerseyNumber = jerseyNumber
        self.goals = goals
        self.ownGoals = ownGoals
        self.monitored = False

    @classmethod
    def from_dict(cls, data: dict):
        id = data["id"]
        name = data["name"]
        substitute = data["substitute"]
        jerseyNumber = data["jerseyNumber"]
        goals = data["goals"]
        ownGoals = data["ownGoals"]
        return cls(id, name, substitute, jerseyNumber, goals, ownGoals)

    def is_player_starting(self, lineups: Lineups) -> bool:
        if lineups:
            for p in lineups.homeLineup:
                if p.id == self.id and not p.substitute:
                    return True
            for p in lineups.awayLineup:
                if p.id == self.id and not p.substitute:
                    return True
        return False


    def get_player_subs_incident(self, subs_incidents: list[SubsIncident]) -> Union[SubsIncident, None]:
        if subs_incidents:
            subs_incident = self.is_player_in(subs_incidents)
            if subs_incident:
                return subs_incident
            subs_incident = self.is_player_out(subs_incidents)
            if subs_incident:
                return subs_incident
        return None




    def is_player_in(self, subs_incidents: list[SubsIncident]) -> Union[SubsIncident, None]:
        for si in subs_incidents:
            if si.playerIn.id == self.id:
                si.subsIncidentType = "in"
                return si
        return None


    def is_player_out(self, subs_incidents: list[SubsIncident]) -> Union[SubsIncident, None]:
        for si in subs_incidents:
            if si.playerOut.id == self.id:
                si.subsIncidentType = "out"
                return si
        return None
            
        


class Incident:
    def __init__(self, minute: int, incidentType: str):
        self.minute = minute
        self.incidentType = incidentType


class SubsIncident(Incident):
    def __init__(self, minute: int, incidentType: str, playerIn: Player, playerOut: Player):
        super().__init__(minute, incidentType)
        self.playerIn = playerIn
        self.playerOut = playerOut
        self.subsIncidentType: Literal["in", "out"]


class Lineups:
    def __init__(self, homeLineup: list[Player],awayLineup: list[Player]):
        self.homeLineup = homeLineup
        self.awayLineup = awayLineup





def format_matches_data(data: Any, date: str) -> list[MatchesByTournament]:
    matches_jq = '[.events[] | {"id": .id, "date": .startTimestamp, "timestamp": .startTimestamp, "status": .status.type, "tournament": {"id": .tournament.uniqueTournament.id, "name": .tournament.name, "country": .tournament.category.name}, "awayTeam": {"name": .awayTeam.name, "id": .awayTeam.id, "score": .awayScore.current}, "homeTeam": {"name": .homeTeam.name, "id": .homeTeam.id, "score": .homeScore.current}} | .date |= strftime("%Y-%m-%d") | select(.date == $today_date)] | group_by(.tournament.id) | map({"tournamentName": (.[0].tournament.name + " (" + .[0].tournament.country + ")"), "matches": [.[]]}) | .[]'
    matches_by_tournament_list = pyjq.all(matches_jq, data, vars={"today_date": date})
    matches_by_tournament_list = [
        MatchesByTournament(
            tournamentName=mbt["tournamentName"],
            matches=[
                Match(
                    id=match["id"],
                    date=match["date"],
                    timestamp=match["timestamp"],
                    status=match["status"],
                    tournament=Tournament(**match["tournament"]),
                    homeTeam=Team(**match["homeTeam"]),
                    awayTeam=Team(**match["awayTeam"])
                ) for match in mbt["matches"]]
        ) for mbt in matches_by_tournament_list
    ]
    return matches_by_tournament_list





def format_lineups_data(data: Any) -> Lineups:
    home_lineups_jq = '.home.players[] | {"name": .player.name, "id": .player.id, "substitute": .substitute, "jerseyNumber": .jerseyNumber, "goals": .statistics.goals, "ownGoals": .statistics.ownGoals}'
    away_lineups_jq = '.away.players[] | {"name": .player.name, "id": .player.id, "substitute": .substitute, "jerseyNumber": .jerseyNumber, "goals": .statistics.goals, "ownGoals": .statistics.ownGoals}'
    home_lineup = pyjq.all(home_lineups_jq, data)
    away_lineup = pyjq.all(away_lineups_jq, data)
    lineups = Lineups(
        homeLineup=[Player(**p) for p in home_lineup], 
        awayLineup=[Player(**p) for p in away_lineup]
    )
    return lineups



def format_subs_incidents_data(data: Any) -> list[SubsIncident]:
    incidents_jq = '.incidents[] | select(.incidentType == "substitution") | {"minute": .time, "incidentType":.incidentType, "playerIn": {"name": .playerIn.name, "id": .playerIn.id, "jerseyNumber": .playerIn.jerseyNumber}, "playerOut": {"name": .playerOut.name, "id": .playerOut.id, "jerseyNumber": .playerOut.jerseyNumber}}'
    incidents = pyjq.all(incidents_jq, data)
    incidents = [
        SubsIncident(
            minute=inc["minute"],
            incidentType=inc["incidentType"],
            playerIn=Player(**inc["playerIn"]),
            playerOut=Player(**inc["playerOut"])
        ) for inc in incidents
    ]
    return incidents

