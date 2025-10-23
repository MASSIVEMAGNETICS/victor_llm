import random

class ConsciousnessLoop:
    """
    A placeholder for the Victor Consciousness Loop v1.1.1.
    This class simulates the core intelligence engine, returning dummy metrics
    to allow for the development and testing of the surrounding runtime components.
    """
    def __init__(self, obs_dim: int, z_dim: int):
        """
        Initializes the placeholder loop.
        The parameters are kept for API compatibility.
        """
        self.obs_dim = obs_dim
        self.z_dim = z_dim
        print(f"Initialized placeholder ConsciousnessLoop (obs_dim={obs_dim}, z_dim={z_dim})")

    def step(self, external_o: float):
        """
        Simulates a single step of the consciousness loop.

        Args:
            external_o: A scalar observation from the environment.

        Returns:
            A tuple containing:
            - A dictionary of dummy metrics.
            - A None value, matching the expected API.
        """
        # Generate dummy metrics for testing purposes
        metrics = {
            "fidelity": random.uniform(0.9, 0.99),
            "sharpness": random.uniform(0.8, 0.95),
            "drift": random.uniform(0.01, 0.05),
            "depth_score": random.uniform(1.5, 2.5),
            "pred_loss": random.uniform(0.1, 0.3),
            "reward": external_o * random.uniform(0.5, 1.5) # Make reward somewhat related to input
        }

        # The second return value is None, as specified in the runner sketch
        return metrics, None