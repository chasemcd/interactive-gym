import collections


class MultiAgentPolicyWrapper:
    def __init__(self, policy_mapping, available_policies, action_space, configs):
        self.policies = {
            a_id: available_policies[p](config=configs[a_id], action_space=action_space)
            for a_id, p in policy_mapping.items()
        }
        self.states = collections.defaultdict(lambda: None)

    def compute_single_action(self, obs, agent_id: str | None = None):
        return self.policies[agent_id].compute_single_action(
            obs=obs, state=self.states[agent_id]
        )
