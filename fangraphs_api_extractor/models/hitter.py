from typing import Optional

from pydantic import Field

from .base_player import BaseProjectionModel, PlayerModel


class HitterProjectionModel(BaseProjectionModel):
    """Base class for hitter projections with fields common across projection systems"""

    # Common batting stats across projection systems
    games: Optional[float] = Field(None, alias="G")
    pa: Optional[float] = Field(None, alias="PA")
    ab: Optional[float] = Field(None, alias="AB")
    h: Optional[float] = Field(None, alias="H")
    singles: Optional[float] = Field(None, alias="1B")
    doubles: Optional[float] = Field(None, alias="2B")
    triples: Optional[float] = Field(None, alias="3B")
    hr: Optional[float] = Field(None, alias="HR")
    r: Optional[float] = Field(None, alias="R")
    rbi: Optional[float] = Field(None, alias="RBI")
    bb: Optional[float] = Field(None, alias="BB")
    ibb: Optional[float] = Field(None, alias="IBB")
    so: Optional[float] = Field(None, alias="SO")
    hbp: Optional[float] = Field(None, alias="HBP")
    sf: Optional[float] = Field(None, alias="SF")
    sh: Optional[float] = Field(None, alias="SH")
    gdp: Optional[float] = Field(None, alias="GDP")
    sb: Optional[float] = Field(None, alias="SB")
    cs: Optional[float] = Field(None, alias="CS")

    # Rate stats
    avg: Optional[float] = Field(None, alias="AVG")
    obp: Optional[float] = Field(None, alias="OBP")
    slg: Optional[float] = Field(None, alias="SLG")
    ops: Optional[float] = Field(None, alias="OPS")
    iso: Optional[float] = Field(None, alias="ISO")
    babip: Optional[float] = Field(None, alias="BABIP")
    woba: Optional[float] = Field(None, alias="wOBA")
    wrc_plus: Optional[float] = Field(None, alias="wRC+")

    # Advanced metrics - include all fields that appear in multiple projection systems
    war: Optional[float] = Field(None, alias="WAR")
    k_percent: Optional[float] = Field(None, alias="K%")
    bb_percent: Optional[float] = Field(None, alias="BB%")
    bb_k: Optional[float] = Field(None, alias="BB/K")
    swstr_percent: Optional[float] = Field(None, alias="SwStr%")

    # Value metrics that appear in multiple systems
    age: Optional[int] = Field(None, alias="Age")
    offense: Optional[float] = Field(None, alias="Offense")
    defense: Optional[float] = Field(None, alias="Defense")
    bsr: Optional[float] = Field(None, alias="BsR")
    w_bsr: Optional[float] = Field(None, alias="wBsR")
    batting: Optional[float] = Field(None, alias="Batting")
    fielding: Optional[float] = Field(None, alias="Fielding")
    replacement: Optional[float] = Field(None, alias="Replacement")
    positional: Optional[float] = Field(None, alias="Positional")
    rar: Optional[float] = Field(None, alias="RAR")
    dollars: Optional[float] = Field(None, alias="Dollars")
    spd: Optional[float] = Field(None, alias="Spd")
    wraa: Optional[float] = Field(None, alias="wRAA")
    wrc: Optional[float] = Field(None, alias="wRC")
    ubr: Optional[float] = Field(None, alias="UBR")
    w_league: Optional[float] = Field(None, alias="wLeague")
    off: Optional[float] = Field(None, alias="Off")
    def_: Optional[float] = Field(None, alias="Def")

    # Additional stats from newer format
    fpts_g: Optional[float] = Field(None, alias="FPTS_G")
    spts_g: Optional[float] = Field(None, alias="SPTS_G")
    woba_sd: Optional[float] = Field(None, alias="woba_sd")
    truetalent_sd: Optional[float] = Field(None, alias="truetalent_sd")
    woba_sd_book: Optional[float] = Field(None, alias="woba_sd_book")
    woba_se: Optional[float] = Field(None, alias="woba_se")
    total_se: Optional[float] = Field(None, alias="total_se")
    uzr: Optional[float] = Field(None, alias="UZR")
    base_running: Optional[float] = Field(None, alias="BaseRunning")
    gdp_runs: Optional[float] = Field(None, alias="GDPRuns")


class HitterSteamerProjectionModel(HitterProjectionModel):
    """Steamer specific projection for hitters"""

    # Fields unique to Steamer projections
    ra_talent_sd: Optional[float] = None
    chance_ra_se: Optional[float] = None
    total_ra_se: Optional[float] = None


class HitterATCProjectionModel(HitterProjectionModel):
    """ATC specific projection for hitters"""

    # Only fields unique to ATC would go here
    pass


class HitterTHEBATProjectionModel(HitterProjectionModel):
    """THE BAT specific projection for hitters"""

    # Only fields unique to THE BAT would go here
    pass


class HitterModel(PlayerModel):
    """Base model for all hitters"""

    # This class only contains fields that are unique to the player
    # but not part of any projection system
    pass
