import random

import chex
import jax
import jax.numpy as jnp
import numpy as np
from luxai2022 import LuxAI2022
from rich import print

import jux.utils
from jux.config import JuxBufferConfig
from jux.state import JuxAction, State
from jux.team import FactionTypes

jnp.set_printoptions(linewidth=500, threshold=10000)


def map_to_aval(pytree):
    return jax.tree_map(lambda x: x.aval, pytree)


state___eq___jitted = jax.jit(chex.assert_max_traces(n=1)(State.__eq__))


class TestState(chex.TestCase):

    def test_from_to_lux(self):
        buf_cfg = JuxBufferConfig(MAX_N_UNITS=30)
        env, actions = jux.utils.load_replay('tests/replay-45702251.json.gz')
        for i in range(10):
            action = next(actions)
            env.step(action)

        lux_state = env.state
        jux_state = State.from_lux(lux_state, buf_cfg)
        assert jux_state == State.from_lux(jux_state.to_lux(), buf_cfg)

    def test_step_late_game(self):
        chex.clear_trace_counter()

        # 1. function to be tested
        _state_step_late_game = jax.jit(chex.assert_max_traces(n=1)(State._step_late_game))

        # 2. prepare an environment
        buf_cfg = JuxBufferConfig(MAX_N_UNITS=100)
        env, actions = jux.utils.load_replay('https://www.kaggleusercontent.com/episodes/45715004.json')

        # skip early stage
        while env.env_steps < 5:
            act = next(actions)
            env.step(act)

        jux_state = State.from_lux(env.state, buf_cfg)

        # 3. some helper functions

        # wrapper for profiling
        def state_step_late_game(jux_state, jux_act):
            return _state_step_late_game(jux_state, jux_act)

        # step
        def step_both(jux_state: State, env: LuxAI2022, lux_act):

            jux_act = jux_state.parse_actions_from_dict(lux_act)
            jux_state = _state_step_late_game(jux_state, jux_act)
            # jnp.array(0).block_until_ready()

            env.step(lux_act)
            lux_state = env.state

            return jux_state, lux_state

        def assert_state_eq(jux_state, lux_state):
            lux_state = State.from_lux(lux_state, buf_cfg)
            assert state___eq___jitted(jux_state, lux_state)

        # warm up jit, for profile only
        state___eq___jitted(jux_state, jux_state)
        state_step_late_game(jux_state, JuxAction.empty(jux_state.env_cfg, buf_cfg))

        # 4. real test starts here
        for i, act in enumerate(actions):
            print(f"steps: {env.env_steps}")
            jux_state, lux_state = step_both(jux_state, env, act)
        assert_state_eq(jux_state, lux_state)

    @chex.variants(with_jit=True, without_jit=True, with_device=True)
    def test_recharge_action(self):
        chex.clear_trace_counter()

        # 1. function to be tested
        state_step_late_game = self.variant(chex.assert_max_traces(n=1)(State._step_late_game))

        # 2. prepare an environment
        buf_cfg = JuxBufferConfig(MAX_N_UNITS=100)

        env, actions = jux.utils.load_replay("https://www.kaggleusercontent.com/episodes/45715004.json")

        # skip first several steps, since it contains no recharge action
        while env.env_steps < 10 + 149:
            act = next(actions)
            env.step(act)

        jux_state = State.from_lux(env.state, buf_cfg)

        # 3. some helper functions

        # step
        def step_both(jux_state: State, env: LuxAI2022, lux_act):

            jux_act = jux_state.parse_actions_from_dict(lux_act)
            jux_state = state_step_late_game(jux_state, jux_act)
            jnp.array(0).block_until_ready()

            env.step(lux_act)
            lux_state = env.state

            return jux_state, lux_state

        def assert_state_eq(jux_state, lux_state):
            lux_state = State.from_lux(lux_state, buf_cfg)
            assert state___eq___jitted(jux_state, lux_state)

        # # warm up jit, for profile only
        # state___eq___jitted(jux_state, jux_state)
        # state_step_late_game(jux_state, JuxAction.empty(jux_state.env_cfg, buf_cfg))

        # 4. real test starts here
        for i, act in zip(range(10), actions):
            print(f"steps: {env.env_steps}")
            jux_state, lux_state = step_both(jux_state, env, act)
            assert_state_eq(jux_state, lux_state)

    @chex.variants(with_jit=True, without_jit=True, with_device=True)
    def test_step_factory_water(self):
        chex.clear_trace_counter()

        # 1. function to be tested
        state_step_late_game = self.variant(chex.assert_max_traces(n=1)(State._step_late_game))

        # 2. prepare an environment
        buf_cfg = JuxBufferConfig(MAX_N_UNITS=100)
        env, actions = jux.utils.load_replay("https://www.kaggleusercontent.com/episodes/45715004.json")
        # The first 905 steps do not contains any FactoryAction.Water, so we skip them.
        while env.env_steps < 435:
            act = next(actions)
            env.step(act)

        jux_state = State.from_lux(env.state, buf_cfg)

        # 3. some helper functions

        # step
        def step_both(jux_state: State, env: LuxAI2022, lux_act):

            jux_act = jux_state.parse_actions_from_dict(lux_act)
            jux_state = state_step_late_game(jux_state, jux_act)
            jnp.array(0).block_until_ready()

            env.step(lux_act)
            lux_state = env.state

            return jux_state, lux_state

        # # warm up jit
        # state___eq___jitted(jux_state, jux_state)
        # state_step_late_game(jux_state, JuxAction.empty(jux_state.env_cfg, buf_cfg))

        def assert_state_eq(jux_state, lux_state):
            lux_state = State.from_lux(lux_state, buf_cfg)
            assert state___eq___jitted(jux_state, lux_state)

        # 4. real test starts here

        # step util end
        for i, act in zip(range(300), actions):
            if env.env_steps % 10 == 0:
                print(f"steps: {env.env_steps}")
                jux_state = State.from_lux(env.state, buf_cfg)
                jux_state, lux_state = step_both(jux_state, env, act)
                assert_state_eq(jux_state, lux_state)
            else:
                env.step(act)

    def test_episode(self):
        chex.clear_trace_counter()
        cases = [
            # Some steps are skipped because of bugs in the official one.
            # episode id and skip steps.
            ('45731509', [177, 178, 238]),  # 177, 178, 238, 713, 734, 776, 821
            ('45740668', [25]),  # 16, 25, 38
            ('45742163', [248, 297, 392]),  # 248, 296, 297, 392

            # the following episodes are moved to tests/test_env.py.
            # ('45740641', []),
            # ('45742007', []),
            # ('45750090', [])
        ]
        buf_cfg = JuxBufferConfig(MAX_N_UNITS=200)

        # 1. function to be tested
        state_step_late_game = jax.jit(chex.assert_max_traces(n=1)(State._step_late_game))

        for episode, skip_steps in cases:
            print(f"episode: {episode}")
            # 2. prepare an environment
            env, actions = jux.utils.load_replay(f'https://www.kaggleusercontent.com/episodes/{episode}.json')

            # skip early stage
            while env.env_steps < 11:
                act = next(actions)
                env.step(act)

            lux_state = env.state
            jux_state = State.from_lux(lux_state, buf_cfg)

            # 3. some helper functions

            # step
            def step_both(jux_state: State, env: LuxAI2022, lux_act):

                jux_act = jux_state.parse_actions_from_dict(lux_act)
                jux_state = state_step_late_game(jux_state, jux_act)

                env.step(lux_act)
                lux_state = env.state

                return jux_state, lux_state

            def assert_state_eq(jux_state, lux_state):
                lux_state = State.from_lux(lux_state, buf_cfg)
                assert state___eq___jitted(jux_state, lux_state)

            # 4. real test starts here
            for i, act in enumerate(actions):
                print(f"steps: {env.env_steps}")
                if env.env_steps in skip_steps:
                    assert_state_eq(jux_state, lux_state)
                    env.step(act)
                    jux_state = State.from_lux(env.state, buf_cfg)
                else:
                    jux_state, lux_state = step_both(jux_state, env, act)
            assert_state_eq(jux_state, lux_state)

    def test_team_lichen_score(self):
        env, actions = jux.utils.load_replay("https://www.kaggleusercontent.com/episodes/45715004.json")
        for act in actions:
            _, lux_rewards, _, _ = env.step(act)
        lux_rewards = jnp.array(list(lux_rewards.values()))

        buf_cfg = JuxBufferConfig(MAX_N_UNITS=200)
        jux_state = State.from_lux(env.state, buf_cfg)

        jux_rewards = jux_state.team_lichen_score()

        assert jnp.array_equal(jux_rewards, lux_rewards)


class TestEarlyStageState(chex.TestCase):

    @chex.variants(with_jit=True, without_jit=True, with_device=True)
    def test_bid_step(self):
        state_bid_step = self.variant(State._bid_step)
        for seed in range(10):
            random.seed(seed)
            env = LuxAI2022()
            obs = env.reset(seed)
            n_factory = (-obs['player_0']['real_env_steps'] - 1) // 2
            init_water_metal = env.env_cfg.INIT_WATER_METAL_PER_FACTORY
            bid_range = (
                -init_water_metal * (n_factory + 1),
                init_water_metal * (n_factory + 1),
            )
            bid_act = {
                'player_0': {
                    'bid': random.randint(*bid_range),
                    'faction': random.choice(list(FactionTypes)).name,
                },
                'player_1': {
                    'bid': random.randint(*bid_range),
                    'faction': random.choice(list(FactionTypes)).name,
                }
            }

            jux_state = State.from_lux(env.state)

            # lux step
            obs = env.step(bid_act)

            # jux step
            def _bid_lux2jux(bid_lux):
                bid = jnp.array(
                    [bid_lux['player_0']['bid'], bid_lux['player_1']['bid']],
                    dtype=jnp.int32,
                )
                faction = jnp.array(
                    [
                        FactionTypes.from_lux(bid_lux['player_0']['faction']),
                        FactionTypes.from_lux(bid_lux['player_1']['faction'])
                    ],
                    dtype=jnp.int32,
                )
                return bid, faction

            bid_act_jux = _bid_lux2jux(bid_act)
            jux_state = state_bid_step(jux_state, *bid_act_jux)
            lux_state = State.from_lux(env.state)

            assert state___eq___jitted(jux_state, lux_state)

    @chex.variants(with_jit=True, without_jit=True, with_device=True)
    def test_factory_placement_step(self):
        state_factory_placement_step = self.variant(State._factory_placement_step)
        for seed in range(10):
            random.seed(seed)

            # create env
            env = LuxAI2022()
            obs = env.reset(seed)

            np.random.seed(seed)
            # skip bid step
            obs, _, _, _ = env.step({
                'player_0': {
                    'bid': np.random.randint(-3, 3),
                    'faction': FactionTypes(0).name,
                },
                'player_1': {
                    'bid': np.random.randint(-3, 3),
                    'faction': FactionTypes(0).name,
                }
            })
            jux_state = State.from_lux(env.state)
            factories_per_team = obs['player_0']['board']['factories_per_team']

            # factory placement step
            for i in range(factories_per_team * 2):
                spawn = np.random.randint(env.env_cfg.map_size, size=(2, )).tolist()
                water = np.random.randint(100, 200)
                metal = np.random.randint(100, 200)
                current_player = 0 if obs['player_0']['teams']['player_0']['place_first'] else 1
                current_player = (current_player + i) % 2

                # create lux act
                lux_act = {
                    'player_0': {
                        'metal': metal,
                        'spawn': spawn,
                        'water': water,
                    },
                    'player_1': {},
                }
                if current_player == 1:
                    lux_act['player_1'] = lux_act['player_0']
                    lux_act['player_0'] = {}

                # create jux act
                jux_act = dict(
                    spawn=jnp.array([
                        lux_act['player_0']['spawn'] if lux_act['player_0'] else [0, 0],
                        lux_act['player_1']['spawn'] if lux_act['player_1'] else [0, 0],
                    ]),
                    water=jnp.array([
                        lux_act['player_0']['water'] if lux_act['player_0'] else 0,
                        lux_act['player_1']['water'] if lux_act['player_1'] else 0,
                    ]),
                    metal=jnp.array([
                        lux_act['player_0']['metal'] if lux_act['player_0'] else 0,
                        lux_act['player_1']['metal'] if lux_act['player_1'] else 0,
                    ]),
                )
                # print(f"{valid = }")
                # print(f"{lux_act = }")
                # valid = obs['player_0']['board']['valid_spawns_mask'][spawn[0], spawn[1]]

                # step
                obs, _, _, _ = env.step(lux_act)
                jux_state = state_factory_placement_step(jux_state, **jux_act)

                lux_state = State.from_lux(env.state)
                # print(f"{jux_state.n_factories = }")
                # print(f"{lux_state.n_factories = }")
                # print(f"{jux_state.teams.init_water = }")
                # print(f"{lux_state.teams.init_water = }")
                # print(f"{jux_state.teams.init_metal = }")
                # print(f"{lux_state.teams.init_metal = }")

                assert state___eq___jitted(jux_state, lux_state)
