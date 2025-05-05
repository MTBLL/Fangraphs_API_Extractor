from typing import Optional, Dict, Any, Union
from pydantic import Field

from .base_player import PlayerModel, BaseProjectionModel


class PitcherProjectionModel(BaseProjectionModel):
    """Base class for pitcher projections with fields common across projection systems"""
    # Common pitching stats across projection systems
    wins: Optional[float] = Field(None, alias="W")
    losses: Optional[float] = Field(None, alias="L")
    games_started: Optional[float] = Field(None, alias="GS")
    games: Optional[float] = Field(None, alias="G")
    saves: Optional[float] = Field(None, alias="SV")
    holds: Optional[float] = Field(None, alias="HLD")
    blown_saves: Optional[float] = Field(None, alias="BS")
    innings_pitched: Optional[float] = Field(None, alias="IP")
    total_batters_faced: Optional[float] = Field(None, alias="TBF")
    hits: Optional[float] = Field(None, alias="H")
    runs: Optional[float] = Field(None, alias="R")
    earned_runs: Optional[float] = Field(None, alias="ER")
    home_runs: Optional[float] = Field(None, alias="HR")
    strikeouts: Optional[float] = Field(None, alias="SO")
    walks: Optional[float] = Field(None, alias="BB")
    intentional_walks: Optional[float] = Field(None, alias="IBB")
    hit_by_pitch: Optional[float] = Field(None, alias="HBP")
    
    # Rate stats
    era: Optional[float] = Field(None, alias="ERA")
    whip: Optional[float] = Field(None, alias="WHIP")
    k_per_9: Optional[float] = Field(None, alias="K/9")
    bb_per_9: Optional[float] = Field(None, alias="BB/9")
    k_per_bb: Optional[float] = Field(None, alias="K/BB")
    hr_per_9: Optional[float] = Field(None, alias="HR/9")
    k_percent: Optional[float] = Field(None, alias="K%")
    bb_percent: Optional[float] = Field(None, alias="BB%")
    k_bb_percent: Optional[float] = Field(None, alias="K-BB%")
    gb_percent: Optional[float] = Field(None, alias="GB%")
    
    # Advanced metrics
    avg_against: Optional[float] = Field(None, alias="AVG")
    babip: Optional[float] = Field(None, alias="BABIP")
    lob_percent: Optional[float] = Field(None, alias="LOB%")
    fip: Optional[float] = Field(None, alias="FIP")
    war: Optional[float] = Field(None, alias="WAR")
    ra9_war: Optional[float] = Field(None, alias="RA9-WAR")
    quality_starts: Optional[float] = Field(None, alias="QS")
    
    # Fantasy points
    fpts_ip: Optional[float] = Field(None, alias="FPTS_IP")
    spts_ip: Optional[float] = Field(None, alias="SPTS_IP")
    
    # Projection metrics
    ra_talent_sd: Optional[float] = None
    chance_ra_se: Optional[float] = None
    total_ra_se: Optional[float] = None


class PitcherSteamerProjectionModel(PitcherProjectionModel):
    """Steamer specific projection for pitchers"""
    # Any fields unique to Steamer would go here
    pass


class PitcherATCProjectionModel(PitcherProjectionModel):
    """ATC specific projection for pitchers"""
    # Only fields unique to ATC would go here
    pass


class PitcherTHEBATProjectionModel(PitcherProjectionModel):
    """THE BAT specific projection for pitchers"""
    # Only fields unique to THE BAT would go here
    pass


class PitcherModel(PlayerModel):
    """Base model for all pitchers"""
    # This class only contains fields that are unique to the player
    # but not part of any projection system
    pass
