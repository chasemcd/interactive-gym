import functools

from cogrid.envs import overcooked
import functools

# from ray.rllib.env import MultiAgentEnv

from cogrid.envs.overcooked import overcooked
from cogrid.envs import registry
from cogrid.feature_space import feature_space
import collections


import copy
from cogrid.feature_space import feature
from cogrid.feature_space import features
from cogrid.feature_space import feature_space
from cogrid.core import grid_utils
from cogrid import cogrid_env
from cogrid.core import grid_object
from cogrid.envs.overcooked import overcooked_grid_objects
from cogrid.envs.overcooked import rewards as overcooked_rewards
from cogrid.envs.overcooked import overcooked_features
from cogrid.core import typing
import numpy as np
from cogrid.core import reward
from cogrid.core import reward
from cogrid.core import actions
from cogrid.core.grid import Grid
from cogrid.envs.overcooked import overcooked_grid_objects
from cogrid.core import typing


class BehaviorFeatures(feature.Feature):
    """A feature that provides the weight coefficient for each reward function."""

    def __init__(self, **kwargs):
        super().__init__(
            low=-np.inf,
            high=np.inf,
            shape=(4,),
            name="overcooked_behavior_features",
            **kwargs,
        )

    def generate(self, env: cogrid_env.CoGridEnv, player_id, **kwargs):
        encoding = np.zeros(self.shape, dtype=np.float32)

        reward_weights = env.reward_weights[player_id]
        for i, reward_id in enumerate(reward_weights.keys()):
            encoding[i] = reward_weights[reward_id]

        return encoding


class OvercookedCollectedBehaviorFeatures(feature.Feature):
    """
    A wrapper class to create all overcooked features as a single array.
    """

    def __init__(self, env: cogrid_env.CoGridEnv, **kwargs):
        num_pots = np.sum(
            [
                int(isinstance(grid_obj, overcooked_grid_objects.Pot))
                for grid_obj in env.grid.grid
            ]
        )
        num_agents = len(env.agent_ids)

        self.shared_features = [
            features.AgentDir(),
            overcooked_features.OvercookedInventory(),
            overcooked_features.NextToCounter(),
            overcooked_features.ClosestObj(
                focal_object_type=overcooked_grid_objects.Onion
            ),
            overcooked_features.ClosestObj(
                focal_object_type=overcooked_grid_objects.Plate
            ),
            overcooked_features.ClosestObj(
                focal_object_type=overcooked_grid_objects.PlateStack
            ),
            overcooked_features.ClosestObj(
                focal_object_type=overcooked_grid_objects.OnionStack
            ),
            overcooked_features.ClosestObj(
                focal_object_type=overcooked_grid_objects.OnionSoup
            ),
            overcooked_features.ClosestObj(
                focal_object_type=overcooked_grid_objects.DeliveryZone
            ),
            overcooked_features.ClosestObj(
                focal_object_type=grid_object.Counter
            ),
            overcooked_features.OrderedPotFeatures(num_pots=num_pots),
            overcooked_features.DistToOtherPlayers(
                num_other_players=len(env.agent_ids) - 1
            ),
            features.AgentPosition(),
        ]

        self.individual_features = [BehaviorFeatures()]

        full_shape = num_agents * np.sum(
            [feature.shape for feature in self.shared_features]
        ) + np.sum([feature.shape for feature in self.individual_features])

        super().__init__(
            low=-np.inf,
            high=np.inf,
            shape=(full_shape,),
            name="overcooked_behavior_features",
            **kwargs,
        )

    def generate(
        self, env: cogrid_env.CoGridEnv, player_id, **kwargs
    ) -> np.ndarray:
        player_encodings = [self.generate_player_encoding(env, player_id)]

        for pid in env.agent_ids:
            if pid == player_id:
                continue
            player_encodings.append(self.generate_player_encoding(env, pid))

        encoding = np.hstack(player_encodings).astype(np.float32)
        encoding = np.hstack(
            [encoding, self.generate_individual_encoding(env, player_id)]
        )
        assert np.array_equal(self.shape, encoding.shape)

        return encoding

    def generate_player_encoding(
        self, env: cogrid_env.CoGridEnv, player_id: str | int
    ) -> np.ndarray:
        encoded_features = []
        for feature in self.shared_features:
            encoded_features.append(feature.generate(env, player_id))

        return np.hstack(encoded_features)

    def generate_individual_encoding(
        self, env: cogrid_env.CoGridEnv, player_id: str | int
    ) -> np.ndarray:
        encoded_features = []
        for feature in self.individual_features:
            encoded_features.append(feature.generate(env, player_id))

        return np.hstack(encoded_features)


feature_space.register_feature(
    "overcooked_behavior_features", OvercookedCollectedBehaviorFeatures
)


class SoupDeliveryActReward(reward.Reward):
    """Provide a reward for delivery an OnionSoup to a DeliveryZone."""

    def __init__(
        self, agent_ids: list[str | int], coefficient: float = 1.0, **kwargs
    ):
        super().__init__(
            name="delivery_act_reward",
            agent_ids=agent_ids,
            coefficient=coefficient,
            **kwargs,
        )

    def calculate_reward(
        self,
        state: Grid,
        agent_actions: dict[typing.AgentID, typing.ActionType],
        new_state: Grid,
    ) -> dict[typing.AgentID, float]:
        """Calcaute the reward for delivering a soup dish.

        :param state: The previous state of the grid.
        :type state: Grid
        :param actions: Actions taken by each agent in the previous state of the grid.
        :type actions: dict[int  |  str, int  |  float]
        :param new_state: The new state of the grid.
        :type new_state: Grid
        """
        # Reward is shared among all agents, so calculate once
        # then distribute to all agents

        individual_rewards = {agent_id: 0 for agent_id in self.agent_ids}

        for agent_id, action in agent_actions.items():
            # Check if agent is performing a PickupDrop action
            if action != actions.Actions.PickupDrop:
                continue

            # Check if an agent is holding an OnionSoup
            agent = state.grid_agents[agent_id]
            agent_holding_soup = any(
                [
                    isinstance(obj, overcooked_grid_objects.OnionSoup)
                    for obj in agent.inventory
                ]
            )

            # Check if the agent is facing a delivery zone
            fwd_pos = agent.front_pos
            fwd_cell = state.get(*fwd_pos)
            agent_facing_delivery = isinstance(
                fwd_cell, overcooked_grid_objects.DeliveryZone
            )

            if agent_holding_soup and agent_facing_delivery:
                individual_rewards[agent_id] += self.coefficient

        return individual_rewards


reward.register_reward("delivery_act_reward", SoupDeliveryActReward)


class OvercookedRewardEnv(overcooked.Overcooked):
    def __init__(self, config, render_mode=None, **kwargs):
        overcooked.Overcooked.__init__(
            self, config, render_mode=render_mode, **kwargs
        )
        self.observation_space = self.observation_spaces[0]
        self.action_space = self.action_spaces[0]
        self.sample_delivery_reward = config.get(
            "sample_delivery_reward", False
        )
        self.default_behavior_weights = config.get(
            "behavior_weights",
            {
                agent_id: {
                    "delivery_reward": 1,
                    "delivery_act_reward": 0,
                    "onion_in_pot_reward": 0,
                    "soup_in_dish_reward": 0,
                }
                for agent_id in self.agents
            },
        )
        self.reward_weights: dict[typing.AgentID, dict[str, float]] = (
            copy.deepcopy(self.default_behavior_weights)
        )

        # MultiAgentEnv.__init__(self)

        self.unshaped_proportion = config.get("unshaped_proportion", 0.95)

        self.enable_weight_randomization = config.get(
            "enable_weight_randomization", True
        )

    def on_reset(self) -> None:
        """Generate new reward weights every reset."""
        super().on_reset()

        if not self.enable_weight_randomization:
            self.reward_weights = copy.deepcopy(self.default_behavior_weights)
            return

        reward_weights = {agent_id: {} for agent_id in self.agent_ids}

        for agent_id in self.agents:
            for reward_id in self.default_behavior_weights[agent_id].keys():
                if (
                    reward_id == "delivery_reward"
                    and not self.sample_delivery_reward
                ) or np.random.random() < self.unshaped_proportion:
                    weight = self.default_behavior_weights[agent_id][reward_id]
                    reward_weights[agent_id][reward_id] = weight
                else:
                    sampled_weight = np.random.normal()

                    reward_weights[agent_id][reward_id] = sampled_weight

        self.reward_weights = reward_weights

    def compute_rewards(
        self,
    ) -> None:
        """Compute the per agent and per component rewards for the current state transition
        using the reward modules provided in the environment configuration.

        The rewards are added to self.per_agent_rewards and self.per_component_rewards.
        """

        for reward in self.rewards:
            calculated_rewards = reward.calculate_reward(
                state=self.prev_grid,
                agent_actions=self.prev_actions,
                new_state=self.grid,
            )

            # Add component rewards to per agent reward
            for agent_id, reward_value in calculated_rewards.items():
                self.per_agent_reward[agent_id] += (
                    reward_value * self.reward_weights[agent_id][reward.name]
                )

            # Save reward by component
            self.per_component_reward[reward.name] = calculated_rewards


reward.register_reward(
    "onion_in_pot_reward_1.0coeff",
    functools.partial(overcooked_rewards.OnionInPotReward),
)

reward.register_reward(
    "soup_in_dish_reward_1.0coeff",
    functools.partial(overcooked_rewards.SoupInDishReward),
)

overcooked_config = {
    "name": "overcooked",
    "num_agents": 2,
    "action_set": "cardinal_actions",
    "features": ["overcooked_behavior_features"],
    "rewards": [
        "delivery_reward",
        "delivery_act_reward",
        "onion_in_pot_reward_1.0coeff",
        "soup_in_dish_reward_1.0coeff",
    ],
    "grid_gen_kwargs": {"load": "overcooked-crampedroom-v0"},
    "max_steps": 1000,
    "unshaped_proportion": 0.95,
    "behavior_weights": {
        agent_id: {
            "delivery_reward": 1,
            "delivery_act_reward": 0,
            "onion_in_pot_reward": 0,
            "soup_in_dish_reward": 0,
        }
        for agent_id in range(2)
    },
}


registry.register(
    "Overcooked-CrampedRoom-RewardObs-V0",
    functools.partial(OvercookedRewardEnv, config=overcooked_config),
)


overcooked_config_80p = {
    "name": "overcooked",
    "num_agents": 2,
    "action_set": "cardinal_actions",
    "features": ["overcooked_behavior_features"],
    "rewards": [
        "delivery_reward",
        "delivery_act_reward",
        "onion_in_pot_reward_1.0coeff",
        "soup_in_dish_reward_1.0coeff",
    ],
    "grid_gen_kwargs": {"load": "overcooked-crampedroom-v0"},
    "max_steps": 1000,
    "unshaped_proportion": 0.80,
    "sample_delivery_reward": True,
    "behavior_weights": {
        agent_id: {
            "delivery_reward": 1,
            "delivery_act_reward": 0,
            "onion_in_pot_reward": 0,
            "soup_in_dish_reward": 0,
        }
        for agent_id in range(2)
    },
}


registry.register(
    "Overcooked-CrampedRoom-RewardObs-80p-V0",
    functools.partial(OvercookedRewardEnv, config=overcooked_config_80p),
)

overcooked_config_unshaped = {
    "name": "overcooked",
    "num_agents": 2,
    "action_set": "cardinal_actions",
    "features": ["overcooked_behavior_features"],
    "rewards": [
        "delivery_reward",
        "delivery_act_reward",
        "onion_in_pot_reward_1.0coeff",
        "soup_in_dish_reward_1.0coeff",
    ],
    "grid_gen_kwargs": {"load": "overcooked-crampedroom-v0"},
    "max_steps": 1000,
    "unshaped_proportion": 1.0,
    "enable_weight_randomization": False,
    "behavior_weights": {
        agent_id: {
            "delivery_reward": 1,
            "delivery_act_reward": 0,
            "onion_in_pot_reward": 0,
            "soup_in_dish_reward": 0,
        }
        for agent_id in range(2)
    },
}


registry.register(
    "Overcooked-CrampedRoom-RewardObs-Unshaped-V0",
    functools.partial(OvercookedRewardEnv, config=overcooked_config_unshaped),
)


overcooked_config_fixed_shaping = {
    "name": "overcooked",
    "num_agents": 2,
    "action_set": "cardinal_actions",
    "features": ["overcooked_behavior_features"],
    "rewards": [
        "delivery_reward",
        "delivery_act_reward",
        "onion_in_pot_reward_1.0coeff",
        "soup_in_dish_reward_1.0coeff",
    ],
    "grid_gen_kwargs": {"load": "overcooked-crampedroom-v0"},
    "max_steps": 1000,
    "unshaped_proportion": 1.0,
    "behavior_weights": {
        agent_id: {
            "delivery_reward": 1,
            "delivery_act_reward": 0.0,
            "onion_in_pot_reward": 0.1,
            "soup_in_dish_reward": 0.3,
        }
        for agent_id in range(2)
    },
}


registry.register(
    "Overcooked-CrampedRoom-RewardObs-FixedShaping-V0",
    functools.partial(
        OvercookedRewardEnv, config=overcooked_config_fixed_shaping
    ),
)
