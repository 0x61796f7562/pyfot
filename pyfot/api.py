from fake_useragent import FakeUserAgent
import requests
from typing import Union
from .data import MatchesByTournament, SubsIncident, Lineups
from .data import format_matches_data, format_lineups_data, format_subs_incidents_data


request_headers = {"user-agent": FakeUserAgent().random}


def get_matches_grouped_by_tournament(date: str) -> Union[list[MatchesByTournament], None]:
    matches_url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
    response = requests.get(matches_url, headers=request_headers)
    if response.status_code == requests.codes.not_found:
        return None
    response.raise_for_status()
    matches_by_tournament = format_matches_data(response.json(), date)
    return matches_by_tournament




def get_lineups(match_id: int) -> Union[Lineups ,None]:
    lineups_url = f"https://www.sofascore.com/api/v1/event/{match_id}/lineups"
    response = requests.get(lineups_url, headers=request_headers)
    if response.status_code == requests.codes.not_found:
        return None
    response.raise_for_status()
    lineups = format_lineups_data(response.json())
    return lineups




def get_substitution_incidents(match_id: int) -> Union[list[SubsIncident] ,None]:
    incidents_url = f"https://www.sofascore.com/api/v1/event/{match_id}/incidents"
    response = requests.get(incidents_url, headers=request_headers)
    if response.status_code == requests.codes.not_found:
        return None
    response.raise_for_status()
    incidents = format_subs_incidents_data(response.json())
    return incidents









def main():
    match_id = 12796559
    player_id = 1544612






if __name__ == "__main__":
    main()









