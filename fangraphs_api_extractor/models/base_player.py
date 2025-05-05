from typing import Any, Dict, Union, Optional, List, ClassVar, Type, ForwardRef
from pydantic import BaseModel, Field, ConfigDict, create_model
from enum import Enum

# Use forward references to avoid circular imports
HitterModel = ForwardRef("HitterModel")
PitcherModel = ForwardRef("PitcherModel")
HitterProjectionModel = ForwardRef("HitterProjectionModel")
HitterSteamerProjectionModel = ForwardRef("HitterSteamerProjectionModel")
HitterATCProjectionModel = ForwardRef("HitterATCProjectionModel")
HitterTHEBATProjectionModel = ForwardRef("HitterTHEBATProjectionModel")
PitcherProjectionModel = ForwardRef("PitcherProjectionModel")
PitcherSteamerProjectionModel = ForwardRef("PitcherSteamerProjectionModel")
PitcherATCProjectionModel = ForwardRef("PitcherATCProjectionModel")
PitcherTHEBATProjectionModel = ForwardRef("PitcherTHEBATProjectionModel")


class ProjectionSource(str, Enum):
    STEAMER = "steamer"
    ATC = "atc"
    THE_BAT = "the_bat"
    ZIPS = "zips"
    DEPTH_CHARTS = "depth_charts"


class BaseProjectionModel(BaseModel):
    """Base class for projection data from different sources"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    # Common projection fields
    season: Optional[str] = Field(None, alias="Season")
    
    # Percentiles (common across projection systems)
    q10: Optional[float] = None
    q20: Optional[float] = None
    q30: Optional[float] = None
    q40: Optional[float] = None
    q50: Optional[float] = None
    q60: Optional[float] = None
    q70: Optional[float] = None
    q80: Optional[float] = None
    q90: Optional[float] = None
    tt_q10: Optional[float] = None
    tt_q20: Optional[float] = None
    tt_q30: Optional[float] = None
    tt_q40: Optional[float] = None
    tt_q50: Optional[float] = None
    tt_q60: Optional[float] = None
    tt_q70: Optional[float] = None
    tt_q80: Optional[float] = None
    tt_q90: Optional[float] = None
    
    # Fantasy points (common across projection systems)
    fpts: Optional[float] = Field(None, alias="FPTS")
    fpts_pa: Optional[float] = Field(None, alias="FPTS_PA")
    fpts_ip: Optional[float] = Field(None, alias="FPTS_IP")
    spts: Optional[float] = Field(None, alias="SPTS")
    spts_pa: Optional[float] = Field(None, alias="SPTS_PA")
    spts_ip: Optional[float] = Field(None, alias="SPTS_IP")


class PlayerModel(BaseModel):
    """Base class for all player types"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    # Basic player identification
    team: str = Field(alias="Team")
    short_name: str = Field(alias="ShortName")
    player_id: str = Field(alias="playerid") 
    player_name: str = Field(alias="PlayerName")
    xmlbam_id: int = Field(alias="xMLBAMID")
    player_ids: str = Field(alias="playerids")
    team_id: int = Field(alias="teamid")
    league: str = Field(alias="League")
    adp: Optional[float] = Field(None, alias="ADP")
    
    # Additional player information from newer format
    position: Optional[float] = Field(None, alias="Pos")
    min_position: Optional[str] = Field(None, alias="minpos")
    player_url: Optional[str] = Field(None, alias="UPURL")
    
    # Dictionary to store projections from different sources
    projections: Dict[str, BaseProjectionModel] = {}

    @classmethod
    def parse_player(cls, data: Dict[str, Any], projection_source: str = "steamer") -> Union[PitcherModel, HitterModel]:
        """Factory method to determine player type and return appropriate instance"""
        from . import (
            HitterModel, PitcherModel,
            HitterProjectionModel, HitterSteamerProjectionModel, HitterATCProjectionModel, HitterTHEBATProjectionModel,
            PitcherProjectionModel, PitcherSteamerProjectionModel, PitcherATCProjectionModel, PitcherTHEBATProjectionModel
        )
        
        # Determine player and projection types
        if "W" in data and "L" in data and "ERA" in data:
            player_cls = PitcherModel
            if projection_source.lower() == "steamer":
                proj_cls = PitcherSteamerProjectionModel
            elif projection_source.lower() == "atc":
                proj_cls = PitcherATCProjectionModel
            elif projection_source.lower() == "the_bat":
                proj_cls = PitcherTHEBATProjectionModel
            else:
                proj_cls = PitcherProjectionModel
        elif "AB" in data and "PA" in data and "RBI" in data:
            player_cls = HitterModel
            if projection_source.lower() == "steamer":
                proj_cls = HitterSteamerProjectionModel
            elif projection_source.lower() == "atc":
                proj_cls = HitterATCProjectionModel
            elif projection_source.lower() == "the_bat":
                proj_cls = HitterTHEBATProjectionModel
            else:
                proj_cls = HitterProjectionModel
        else:
            raise ValueError(f"Unknown player type from data: {list(data.keys())[:10]}")
        
        # Get field info from pydantic models
        player_fields = {field.alias or name: field for name, field in player_cls.__fields__.items()}
        
        # Extract player data 
        player_data = {}
        for k, v in data.items():
            if k in player_fields or k in player_cls.__fields__:
                player_data[k] = v
        
        # Create player instance
        player = player_cls.parse_obj(player_data)
        
        # Create projection instance
        projection = proj_cls.parse_obj(data)
        
        # Add projection to player
        player.projections[projection_source] = projection
        
        return player
