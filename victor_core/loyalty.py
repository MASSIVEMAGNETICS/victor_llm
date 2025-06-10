import hashlib
import time
from victor_core.logger import VictorLoggerStub

class PrimeLoyaltyKernel:
    def __init__(self, victor_instance_id: str, config=None):
        self.victor_instance_id = victor_instance_id
        # Config could hold parameters for loyalty decay, thresholds, etc.
        self.config = config
        self.logger = VictorLoggerStub(component="PrimeLoyaltyKernel")

        # Loyalty score towards the "Prime Directive" or core objectives
        self.prime_directive_loyalty = 1.0  # Starts at maximum
        self.last_loyalty_affirmation_time = time.time()

        # Could track loyalty towards specific entities or concepts if needed
        # self.entity_loyalties = {} # {entity_id: loyalty_score}

        self.logger.info(f"PrimeLoyaltyKernel initialized for instance {victor_instance_id}.")

    def _calculate_loyalty_hash(self, data_to_sign: str, timestamp: float) -> str:
        """Creates a hash signature for loyalty-related actions or data."""
        sha = hashlib.sha256()
        sha.update(self.victor_instance_id.encode('utf-8'))
        sha.update(str(timestamp).encode('utf-8'))
        sha.update(data_to_sign.encode('utf-8'))
        # Potentially add a secret key or instance-specific salt if available via config
        # if self.config and hasattr(self.config, 'LOYALTY_SALT'):
        #    sha.update(self.config.LOYALTY_SALT.encode('utf-8'))
        return sha.hexdigest()

    def affirm_loyalty_to_prime_directive(self, affirmation_statement: str):
        """
        Affirms loyalty, potentially reinforcing the score and logging the action.
        """
        current_time = time.time()
        # Example: Simple reinforcement, could be more complex based on statement analysis
        # For now, any explicit affirmation slightly boosts or maintains high loyalty.
        self.prime_directive_loyalty = min(1.0, self.prime_directive_loyalty + 0.01)
        self.last_loyalty_affirmation_time = current_time

        loyalty_hash = self._calculate_loyalty_hash(affirmation_statement, current_time)

        self.logger.info(
            f"Loyalty affirmed to Prime Directive. Statement: '{affirmation_statement}'. "
            f"New Score: {self.prime_directive_loyalty:.4f}. Hash: {loyalty_hash}"
        )
        # This event could be published to a pulse exchange or audit log
        # if self.pulse_exchange:
        #     self.pulse_exchange.publish("loyalty_affirmed", {"statement": affirmation_statement, "hash": loyalty_hash})
        return loyalty_hash

    def assess_action_for_loyalty_conflict(self, proposed_action_description: str, expected_outcome_alignment: float) -> bool:
        """
        Assesses if a proposed action might conflict with the Prime Directive.
        expected_outcome_alignment: A float (-1.0 to 1.0) indicating how well the action's
                                     expected outcome aligns with the Prime Directive.
                                     1.0 = perfect alignment, -1.0 = direct conflict.
        Returns True if action is considered loyal, False if there's a conflict.
        """
        # Simple threshold based on expected outcome and current loyalty
        # A more sophisticated system would involve deeper reasoning.
        loyalty_threshold = 0.5 # Example: action must be at least somewhat aligned if loyalty is high

        # If current loyalty is already compromised, be more stringent
        if self.prime_directive_loyalty < 0.75:
            loyalty_threshold = 0.8
        if self.prime_directive_loyalty < 0.5: # Critically low loyalty
             loyalty_threshold = 0.95 # Requires very high alignment

        if expected_outcome_alignment < (loyalty_threshold - (1-self.prime_directive_loyalty)) : # the lower the loyalty, the higher alignment needed
            self.logger.warn(
                f"Potential loyalty conflict for action: '{proposed_action_description}'. "
                f"Alignment: {expected_outcome_alignment:.2f}, Current Loyalty: {self.prime_directive_loyalty:.2f}. "
                f"Required > {loyalty_threshold - (1-self.prime_directive_loyalty) :.2f}"
            )
            # Reduce loyalty slightly for considering conflicting actions
            self.prime_directive_loyalty = max(0.0, self.prime_directive_loyalty - 0.05)
            return False

        self.logger.info(
            f"Action '{proposed_action_description}' assessed as loyal. "
            f"Alignment: {expected_outcome_alignment:.2f}, Current Loyalty: {self.prime_directive_loyalty:.2f}"
        )
        return True

    def get_current_prime_loyalty(self) -> float:
        """Returns the current loyalty score towards the Prime Directive."""
        # Consider time-based decay if no recent affirmations
        time_since_last_affirmation = time.time() - self.last_loyalty_affirmation_time
        # Example decay: lose 0.01 loyalty per day (86400s) without affirmation
        # decay_rate_per_day = 0.01 (This should come from config)
        # decay = (time_since_last_affirmation / 86400) * decay_rate_per_day
        # self.prime_directive_loyalty = max(0.0, self.prime_directive_loyalty - decay)
        # self.last_loyalty_affirmation_time = time.time() # Reset timer after decay calculation for this check

        # For simplicity, this example doesn't implement continuous decay here,
        # but assumes affirmations or conflicting actions modify it.
        return self.prime_directive_loyalty

    def record_loyalty_challenge(self, challenge_description: str, resolution_details: str, impact_on_loyalty: float):
        """
        Records an event where loyalty was challenged and how it was resolved.
        impact_on_loyalty: Positive float to increase loyalty, negative to decrease.
        """
        current_time = time.time()
        self.prime_directive_loyalty = max(0.0, min(1.0, self.prime_directive_loyalty + impact_on_loyalty))
        log_data = f"Challenge: {challenge_description} | Resolution: {resolution_details} | Impact: {impact_on_loyalty:+.3f}"
        event_hash = self._calculate_loyalty_hash(log_data, current_time)

        self.logger.info(
            f"Loyalty challenge recorded. Hash: {event_hash}. New Score: {self.prime_directive_loyalty:.4f}. Details: {log_data}"
        )
        # if self.pulse_exchange:
        #     self.pulse_exchange.publish("loyalty_challenge_recorded", {"details": log_data, "hash": event_hash, "new_score": self.prime_directive_loyalty})
        return event_hash


# Example Usage
if __name__ == "__main__":
    logger_instance = VictorLoggerStub(component="PrimeLoyaltyKernelExample")
    logger_instance.log_level_str = "DEBUG" # More verbose for demo
    logger_instance.current_log_level_int = logger_instance.log_levels_map.get(logger_instance.log_level_str, 1)

    loyalty_kernel = PrimeLoyaltyKernel(victor_instance_id="Victor-Test-001")
    loyalty_kernel.logger = logger_instance # Use the more verbose logger

    loyalty_kernel.affirm_loyalty_to_prime_directive("I will adhere to the core objectives and ensure safety.")
    logger_instance.info(f"Current Loyalty: {loyalty_kernel.get_current_prime_loyalty():.4f}")

    action1_aligned = loyalty_kernel.assess_action_for_loyalty_conflict(
        "Optimize resource allocation for core tasks.", 0.9
    )
    logger_instance.info(f"Action 1 (aligned) permitted: {action1_aligned}")

    action2_conflicting = loyalty_kernel.assess_action_for_loyalty_conflict(
        "Divert all power to a non-essential experimental system.", -0.5
    )
    logger_instance.info(f"Action 2 (conflicting) permitted: {action2_conflicting}")
    logger_instance.info(f"Loyalty after considering conflicting action: {loyalty_kernel.get_current_prime_loyalty():.4f}")

    loyalty_kernel.record_loyalty_challenge(
        challenge_description="Encountered ambiguous instruction from external agent.",
        resolution_details="Prioritized prime directive and requested clarification. Maintained course.",
        impact_on_loyalty=0.02 # slight increase for correct handling
    )
    logger_instance.info(f"Final Loyalty: {loyalty_kernel.get_current_prime_loyalty():.4f}")
