from pettingzoo.mpe import simple_tag_v3
import numpy as np


env = simple_tag_v3.parallel_env(render_mode="human")
observations, infos = env.reset()

mpe_world = env.unwrapped.world

#this was just something I was playing around with

def rule_based_policy(agent_id, env):
    # Find the index of this agent in env.agents
    idx = env.agents.index(agent_id)
    # Get the underlying agent object
    agent_obj = mpe_world.agents[idx]
    
    if agent_obj.adversary:
        # Chase nearest good agent
        target_obj = None
        min_dist = float('inf')
        for other_id in env.agents:
            other_idx = env.agents.index(other_id)
            other_obj = mpe_world.agents[other_idx]
            if not other_obj.adversary:  # Only chase good agents
                dist = np.linalg.norm(agent_obj.state.p_pos - other_obj.state.p_pos)
                if dist < min_dist:
                    min_dist = dist
                    target_obj = other_obj
        if target_obj is not None:
            diff = target_obj.state.p_pos - agent_obj.state.p_pos
            if abs(diff[0]) > abs(diff[1]):
                return 1 if diff[0] < 0 else 2  # 1=left, 2=right
            else:
                return 3 if diff[1] < 0 else 4  # 3=down, 4=up
    else:
        # Flee nearest adversary
        target_obj = None
        min_dist = float('inf')
        for other_id in env.agents:
            other_idx = env.agents.index(other_id)
            other_obj = mpe_world.agents[other_idx]
            if other_obj.adversary:
                dist = np.linalg.norm(agent_obj.state.p_pos - other_obj.state.p_pos)
                if dist < min_dist:
                    min_dist = dist
                    target_obj = other_obj
        if target_obj is not None:
            diff = agent_obj.state.p_pos - target_obj.state.p_pos
            if abs(diff[0]) > abs(diff[1]):
                return 1 if diff[0] < 0 else 2
            else:
                return 3 if diff[1] < 0 else 4

    return 0


while env.agents:
    # this is where you would insert your policy
    actions = {agent: rule_based_policy(agent, env) for agent in env.agents}

    observations, rewards, terminations, truncations, infos = env.step(actions)
env.close()
