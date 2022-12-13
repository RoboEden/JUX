from dataclasses import dataclass
from enum import IntEnum
from typing import NamedTuple, Union

import jax.numpy as jnp
from jax import Array
from luxai2022.team import FactionTypes as LuxFactionTypes
from luxai2022.team import Team as LuxTeam

from jux.config import JuxBufferConfig

INT32_MAX = jnp.iinfo(jnp.int32).max


class FactionTypes(IntEnum):
    AlphaStrike = 0
    MotherMars = 1
    TheBuilders = 2
    FirstMars = 3

    @classmethod
    def from_lux(cls, lux_faction: Union[str, LuxFactionTypes]) -> "FactionTypes":
        if isinstance(lux_faction, str):
            return cls[lux_faction]
        elif isinstance(lux_faction, LuxFactionTypes):
            return cls(lux_faction.value.faction_id)
        else:
            raise ValueError(f"Unsupport type {type(lux_faction)}: {lux_faction}.")

    def to_lux(self) -> LuxFactionTypes:
        return LuxFactionTypes[self.name]


@dataclass
class FactionInfo:
    color: str = "none"
    alt_color: str = "red"
    faction_id: int = -1


FactionTypes.AlphaStrike.color = "yellow"
FactionTypes.AlphaStrike.faction_id = int(FactionTypes.AlphaStrike)
FactionTypes.AlphaStrike.alt_color = "red"

FactionTypes.MotherMars.color = "green"
FactionTypes.MotherMars.faction_id = int(FactionTypes.MotherMars)
FactionTypes.MotherMars.alt_color = "red"

FactionTypes.TheBuilders.color = "blue"
FactionTypes.TheBuilders.faction_id = int(FactionTypes.TheBuilders)
FactionTypes.TheBuilders.alt_color = "red"

FactionTypes.FirstMars.color = "red"
FactionTypes.FirstMars.faction_id = int(FactionTypes.FirstMars)
FactionTypes.FirstMars.alt_color = "red"


class Team(NamedTuple):
    faction: FactionTypes
    team_id: int
    # agent: str # weather we need it?
    init_water: int
    init_metal: int
    factories_to_place: int

    # TODO: remove factory_strains and n_factory, because they are redundant
    # with State.factories.unit_id and State.n_factories
    factory_strains: Array  # int[MAX_N_FACTORIES], factory_id belonging to this team
    n_factory: int  # usually MAX_FACTORIES or MAX_FACTORIES + 1

    @classmethod
    def new(cls, team_id: int, faction: FactionTypes, buf_cfg: JuxBufferConfig) -> "Team":
        return cls(
            faction=jnp.int32(faction),
            team_id=jnp.int32(team_id),
            init_water=jnp.int32(0),
            init_metal=jnp.int32(0),
            factories_to_place=jnp.int32(0),
            factory_strains=jnp.full(buf_cfg.MAX_N_FACTORIES, fill_value=INT32_MAX),
            n_factory=jnp.int32(0),
        )

    @classmethod
    def from_lux(cls, lux_team: LuxTeam, buf_cfg: JuxBufferConfig) -> "Team":
        factory_strains = jnp.full(buf_cfg.MAX_N_FACTORIES, fill_value=INT32_MAX)

        n_factory = len(lux_team.factory_strains)
        factory_strains = factory_strains.at[:n_factory].set(jnp.array(lux_team.factory_strains, dtype=jnp.int32))
        return cls(
            faction=jnp.int32(FactionTypes.from_lux(lux_team.faction)),
            team_id=jnp.int32(lux_team.team_id),
            init_water=jnp.int32(lux_team.init_water),
            init_metal=jnp.int32(lux_team.init_metal),
            factories_to_place=jnp.int32(lux_team.factories_to_place),
            factory_strains=factory_strains,
            n_factory=jnp.int32(n_factory),
        )

    def to_lux(self, place_first: bool) -> LuxTeam:
        lux_team = LuxTeam(
            team_id=int(self.team_id),
            agent=f'player_{int(self.team_id)}',
            faction=FactionTypes(self.faction).to_lux(),
        )
        lux_team.init_water = int(self.init_water)
        lux_team.init_metal = int(self.init_metal)
        lux_team.factories_to_place = int(self.factories_to_place)
        lux_team.factory_strains = self.factory_strains[:self.n_factory].tolist()
        lux_team.place_first = place_first
        return lux_team

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Team):
            return False
        return ((self.faction == __o.faction) & (self.team_id == __o.team_id) & (self.init_water == __o.init_water)
                & (self.init_metal == __o.init_metal) & (self.factories_to_place == __o.factories_to_place)
                & (self.n_factory == __o.n_factory)
                & jnp.array_equal(self.factory_strains, __o.factory_strains))
