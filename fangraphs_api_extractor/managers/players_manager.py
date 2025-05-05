from typing import List

from fangraphs_api_extractor.models.base_player import PlayerModel


def parse_players(data) -> List[PlayerModel]:
    players = []
    unnested_data = data["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]
    for player_data in unnested_data:
        player = PlayerModel.parse_player(player_data)
        players.append(player)
    return players
