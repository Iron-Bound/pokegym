from pdb import set_trace as T
from gymnasium import Env, spaces
import numpy as np

from collections import defaultdict
import io, os
import random
import math

from pokegym.pyboy_binding import (
    ACTIONS,
    make_env,
    open_state_file,
    load_pyboy_state,
    run_action_on_emulator,
)
from pokegym import ram_map, game_map


def play():
    """Creates an environment and plays it"""
    env = Environment(
        rom_path="pokemon_red.gb",
        state_path=None,
        headless=False,
        disable_input=False,
        sound=False,
        sound_emulated=False,
        verbose=True,
    )

    env.reset()
    env.game.set_emulation_speed(1)

    # Display available actions
    print("Available actions:")
    for idx, action in enumerate(ACTIONS):
        print(f"{idx}: {action}")

    # Create a mapping from WindowEvent to action index
    window_event_to_action = {
        "PRESS_ARROW_DOWN": 0,
        "PRESS_ARROW_LEFT": 1,
        "PRESS_ARROW_RIGHT": 2,
        "PRESS_ARROW_UP": 3,
        "PRESS_BUTTON_A": 4,
        "PRESS_BUTTON_B": 5,
        "PRESS_BUTTON_START": 6,
        "PRESS_BUTTON_SELECT": 7,
        # Add more mappings if necessary
    }

    while True:
        # Get input from pyboy's get_input method
        input_events = env.game.get_input()
        env.game.tick()
        env.render()
        if len(input_events) == 0:
            continue

        for event in input_events:
            event_str = str(event)
            if event_str in window_event_to_action:
                action_index = window_event_to_action[event_str]
                observation, reward, done, _, info = env.step(
                    action_index, fast_video=False
                )

                # Check for game over
                if done:
                    print(f"{done}")
                    break

                # Additional game logic or information display can go here
                print(f"new Reward: {reward}\n")


class Base:
    def __init__(
        self,
        rom_path="pokemon_red.gb",
        state_path=None,
        headless=True,
        quiet=False,
        **kwargs,
    ):
        """Creates a PokemonRed environment"""
        if state_path is None:
            state_path = __file__.rstrip("environment.py") + "saves"

        self.game, self.screen = make_env(rom_path, headless, quiet, **kwargs)

        self.initial_states = list()
        for file in os.listdir(state_path):
            if file.endswith(".state"):
                self.initial_states.append(
                    open_state_file(os.path.join(state_path, file))
                )

        self.headless = headless
        self.mem_padding = 2
        self.memory_shape = 80
        self.use_screen_memory = True
        self.window = None

        R, C = self.screen.raw_screen_buffer_dims()
        self.obs_size = (R // 2, C // 2)

        if self.use_screen_memory:
            self.screen_memory = defaultdict(
                lambda: np.zeros((255, 255, 1), dtype=np.uint8)
            )
            self.obs_size += (4,)
            self.window = None
        else:
            self.obs_size += (3,)
        self.observation_space = spaces.Box(
            low=0, high=255, dtype=np.uint8, shape=self.obs_size
        )
        self.action_space = spaces.Discrete(len(ACTIONS))

    def save_state(self):
        state = io.BytesIO()
        state.seek(0)
        self.game.save_state(state)
        self.initial_states.append(state)

    def load_random_state(self):
        rand_idx = random.randint(0, len(self.initial_states) - 1)
        return self.initial_states[rand_idx]

    def reset(self, seed=None, options=None):
        """Resets the game. Seeding is NOT supported"""
        load_pyboy_state(self.game, self.load_random_state())
        return self.screen.screen_ndarray(), {}

    def get_fixed_window(self, arr, y, x, window_size):
        height, width, _ = arr.shape
        h_w, w_w = window_size[0] // 2, window_size[1] // 2

        y_min = max(0, y - h_w)
        y_max = min(height, y + h_w + (window_size[0] % 2))
        x_min = max(0, x - w_w)
        x_max = min(width, x + w_w + (window_size[1] % 2))

        # window = arr[y_min:y_max, x_min:x_max]

        pad_top = h_w - (y - y_min)
        pad_bottom = h_w + (window_size[0] % 2) - 1 - (y_max - y - 1)
        pad_left = w_w - (x - x_min)
        pad_right = w_w + (window_size[1] % 2) - 1 - (x_max - x - 1)

        self.window = np.pad(
            arr[y_min:y_max, x_min:x_max],
            ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)),
            mode="constant",
        )
        # return self.window

    def render(self):
        if self.use_screen_memory:
            r, c, map_n = ram_map.position(self.game)
            # Update tile map
            mmap = self.screen_memory[map_n]
            if 0 <= r <= 254 and 0 <= c <= 254:
                mmap[r, c] = 255

            self.get_fixed_window(mmap, r, c, self.observation_space.shape)
            return np.concatenate(
                (self.screen.screen_ndarray()[::2, ::2], self.window),
                axis=2,
            )
        else:
            return self.screen.screen_ndarray()[::2, ::2]

    def step(self, action):
        run_action_on_emulator(self.game, self.screen, ACTIONS[action], self.headless)
        return self.render(), 0, False, False, {}

    def close(self):
        self.game.stop(False)


class Environment(Base):
    def __init__(
        self,
        rom_path="pokemon_red.gb",
        state_path=None,
        headless=True,
        quiet=False,
        verbose=False,
        **kwargs,
    ):
        super().__init__(rom_path, state_path, headless, quiet, **kwargs)
        self.counts_map = np.zeros((444, 436))
        self.verbose = verbose

    def reset(self, seed=None, options=None, max_episode_steps=20480, reward_scale=4.0):
        """Resets the game. Seeding is NOT supported"""
        load_pyboy_state(self.game, self.load_random_state())

        if self.use_screen_memory:
            self.screen_memory = defaultdict(
                lambda: np.zeros((255, 255, 1), dtype=np.uint8)
            )
        self.time = 0
        self.max_episode_steps = max_episode_steps
        self.reward_scale = reward_scale
        self.prev_map_n = None

        self.max_events = 0
        self.max_level_sum = 0
        self.max_opponent_level = 0

        self.seen_coords = set()
        self.seen_maps = set()

        self.death_count = 0
        self.total_healing = 0
        self.last_hp = 1.0
        self.last_party_size = 1
        self.last_reward = None

        return self.render(), {}

    def step(self, action, fast_video=True):
        run_action_on_emulator(
            self.game,
            self.screen,
            ACTIONS[action],
            self.headless,
            fast_video=fast_video,
        )
        self.time += 1

        # Exploration reward
        r, c, map_n = ram_map.position(self.game)
        self.seen_coords.add((r, c, map_n))

        if map_n != self.prev_map_n:
            self.prev_map_n = map_n
            if map_n not in self.seen_maps:
                self.seen_maps.add(map_n)
                # self.save_state()

        exploration_reward = 0.01 * len(self.seen_coords)
        glob_r, glob_c = game_map.local_to_global(r, c, map_n)
        try:
            self.counts_map[glob_r, glob_c] += 1
        except:
            pass

        # Level reward
        party_size, party_levels = ram_map.party(self.game)
        self.max_level_sum = max(self.max_level_sum, sum(party_levels))
        level_reward = sum([l * 1 * math.log(l) for l in party_levels])

        # Healing and death rewards
        hp = ram_map.hp(self.game)
        hp_delta = hp - self.last_hp
        party_size_constant = party_size == self.last_party_size

        # Only reward if not reviving at pokecenter
        if hp_delta > 0 and party_size_constant and not self.is_dead:
            self.total_healing += hp_delta

        # Dead if hp is zero
        if hp <= 0 and self.last_hp > 0:
            self.death_count += 1
            self.is_dead = True
        elif hp > 0.01:  # TODO: Check if this matters
            self.is_dead = False

        # Update last known values for next iteration
        self.last_hp = hp
        self.last_party_size = party_size

        # Set rewards
        healing_reward = self.total_healing * 2
        death_reward = -0.05 * self.death_count

        # Opponent level reward
        max_opponent_level = max(ram_map.opponent(self.game))
        self.max_opponent_level = max(self.max_opponent_level, max_opponent_level)
        opponent_level_reward = 0.2 * self.max_opponent_level

        # Badge reward
        badges = ram_map.badges(self.game)
        badges_reward = 10 * badges

        # Save Bill
        bill_state = ram_map.saved_bill(self.game)
        bill_reward = 10 * bill_state

        # Event reward
        events = ram_map.events(self.game)
        self.max_events = max(self.max_events, events)
        event_reward = self.max_events

        money = ram_map.money(self.game)

        reward = self.reward_scale * (
            event_reward
            + bill_reward
            + level_reward
            + opponent_level_reward
            + death_reward
            + badges_reward
            + healing_reward
            + exploration_reward
        )

        # Subtract previous reward
        # TODO: Don't record large cumulative rewards in the first place
        if self.last_reward is None:
            reward = 0
            self.last_reward = 0
        else:
            nxt_reward = reward
            reward -= self.last_reward
            self.last_reward = nxt_reward

        info = {}
        done = self.time >= self.max_episode_steps
        if done:
            info = {
                "reward": {
                    "delta": reward,
                    "event": event_reward,
                    "level": level_reward,
                    "opponent_level": opponent_level_reward,
                    "death": death_reward,
                    "badges": badges_reward,
                    "bill_saved": bill_reward,
                    "healing": healing_reward,
                    "exploration": exploration_reward,
                },
                "maps_explored": len(self.seen_maps),
                "party_size": party_size,
                "highest_pokemon_level": max(party_levels),
                "total_party_level": sum(party_levels),
                "deaths": self.death_count,
                "bill_saved": bill_state,
                "badge_1": float(badges >= 1),
                "badge_2": float(badges >= 2),
                "event": events,
                "money": money,
                "pokemon_exploration_map": self.counts_map,
            }

        if self.verbose:
            print(
                f"steps: {self.time}",
                f"exploration reward: {exploration_reward}",
                f"level_Reward: {level_reward}",
                f"healing: {healing_reward}",
                f"death: {death_reward}",
                f"op_level: {opponent_level_reward}",
                f"badges reward: {badges_reward}",
                f"event reward: {event_reward}",
                f"money: {money}",
                f"ai reward: {reward}",
                f"Info: {info}",
            )

        return self.render(), reward, done, done, info
