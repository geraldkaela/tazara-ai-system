from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.baseline_scheduler import BaselineScheduler
from reinforcement_rl.agent import QLearningAgent

def evaluate_uploaded_routes(routes):
    """
    routes = [
        {"route": "...", "cargo": 320, "priority": "high"},
        ...
    ]
    """

    # Build environment dynamically
    env = TazaraEnv(
        external_routes=routes,
        num_trains=5
    )

    # -------- BASELINE --------
    baseline = BaselineScheduler(env)
    baseline_result = baseline.run(days=1)

    # -------- RL AGENT --------
    agent = QLearningAgent(
        action_size=env.action_space,
        state_size=env.state_space
    )

    rl_result = agent.evaluate(env, days=1)

    # -------- COMPARISON --------
    if rl_result["total_reward"] > baseline_result["total_reward"]:
        best = "RL"
        best_schedule = rl_result
    else:
        best = "Baseline"
        best_schedule = baseline_result

    return {
        "recommended_model": best,
        "baseline": baseline_result,
        "rl": rl_result,
        "best_schedule": best_schedule
    }
