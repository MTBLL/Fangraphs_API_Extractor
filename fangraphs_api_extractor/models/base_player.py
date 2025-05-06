from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, ForwardRef, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fangraphs_api_extractor.utils import normalize_string

T = TypeVar("T", bound="PlayerModel")
# Use forward references to avoid circular imports
if TYPE_CHECKING:
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

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

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

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    # Basic player identification
    team: str = Field(alias="Team")  # Will be handled by validator
    playerid: str = Field(alias="playerid")
    name: str = Field(alias="PlayerName")
    xmlbam_id: int = Field(alias="xMLBAMID")
    team_id: int = Field(alias="teamid")
    adp: Optional[float] = Field(None, alias="ADP")

    @field_validator("team", mode="before")
    @classmethod
    def handle_null_team(cls, v):
        """Convert None team values to 'FA' for free agents"""
        if v is None:
            return "FA"
        return v

    @field_validator("team_id", "xmlbam_id", mode="before")
    @classmethod
    def handle_null_ids(cls, v):
        """Convert None ID values to -1"""
        if v is None:
            return -1
        return v

    # Additional player information from newer format
    min_position: Optional[str] = Field(None, alias="minpos")
    upurl: Optional[str] = Field(None, alias="UPURL")

    @property
    def ascii_name(self) -> str:
        """Return the name with accents removed (ASCII-only version)"""
        return normalize_string(self.name)

    @property
    def slug(self) -> str:
        """
        Generate a URL-safe slug for the player using the ASCII version of the name.
        This removes accents and non-ASCII characters for URL compatibility.
        """
        # Use ascii_name to ensure no accents or non-ASCII characters
        # then drop any periods and replace spaces with hyphens
        return self.ascii_name.lower().replace(".", "").replace(" ", "-")

    @property
    def stats_api(self) -> str:
        """
        Return the transformed URL with .json added before the query string.

        Example:
        - Input: "/players/corbin-carroll/25878/stats?position=OF"
        - Output: "/players/corbin-carroll/25878/stats.json?position=OF"
        """
        # Pitchers don't have upurls, so we need to build for them
        if not self.upurl:
            return f"/players/{self.slug}/{self.playerid}/stats.json?position=P"

        # Handle URL transformation
        return self.upurl.replace("stats", "stats.json")

    # Dictionary to store projections from different sources
    projections: Dict[str, BaseProjectionModel] = {}

    def model_dump_json(self, **kwargs) -> str:
        """
        Serialize the model to a JSON string with indentation for readability.

        Args:
            **kwargs: Additional kwargs passed to model_dump

        Returns:
            str: JSON string representation of the model
        """
        import json

        # Set default values for JSON serialization if not provided
        kwargs.setdefault("indent", 2)
        kwargs.setdefault("exclude_none", True)

        # Get model as dict
        data = self.model_dump(**kwargs)

        # Convert to JSON string
        return json.dumps(
            data,
            **{
                k: v
                for k, v in kwargs.items()
                if k in ["indent", "ensure_ascii", "sort_keys"]
            },
        )

    @classmethod
    def parse_player(
        cls, data: Dict[str, Any], projection_source: str = "steamer"
    ) -> Any:
        """Factory method to determine player type and return appropriate instance"""
        from typing import Type

        from . import (
            HitterATCProjectionModel,
            HitterModel,
            HitterProjectionModel,
            HitterSteamerProjectionModel,
            HitterTHEBATProjectionModel,
            PitcherATCProjectionModel,
            PitcherModel,
            PitcherProjectionModel,
            PitcherSteamerProjectionModel,
            PitcherTHEBATProjectionModel,
        )

        # Determine player and projection types
        player_cls: Type[PitcherModel | HitterModel]
        proj_cls: Type[
            PitcherSteamerProjectionModel
            | PitcherATCProjectionModel
            | PitcherTHEBATProjectionModel
            | PitcherProjectionModel
            | HitterSteamerProjectionModel
            | HitterATCProjectionModel
            | HitterTHEBATProjectionModel
            | HitterProjectionModel
        ]

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

        # Extract player data
        player_data = {}
        for k, v in data.items():
            player_data[k] = v

        # Create player instance
        player = player_cls.model_validate(player_data)

        # Create projection instance
        projection = proj_cls.model_validate(data)

        # Add projection to player
        player.projections[projection_source] = projection

        return player
