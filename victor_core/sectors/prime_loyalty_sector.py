import asyncio
from victor_core.sectors.base import VictorSector
from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
from victor_core.loyalty import PrimeLoyaltyKernel
# from victor_core.config import ASIConfigCore # If creator_signature/approved_entities come from config

class PrimeLoyaltySector(VictorSector):
    def __init__(self, pulse_exchange_instance: BrainFractalPulseExchange, name: str, asi_core_ref,
                 creator_signature: str = "DefaultCreatorSig",
                 approved_entities: list[str] = None):
        super().__init__(pulse_exchange_instance, name, asi_core_ref)

        # Get creator_signature and approved_entities from asi_core_ref.config if available,
        # otherwise use constructor parameters or defaults.
        config = getattr(self.asi_core, 'config', None)
        if config:
            final_creator_signature = getattr(config, 'CREATOR_SIGNATURE', creator_signature)
            final_approved_entities = getattr(config, 'APPROVED_ENTITIES', approved_entities if approved_entities else [])
        else:
            final_creator_signature = creator_signature
            final_approved_entities = approved_entities if approved_entities else []

        # Initialize the PrimeLoyaltyKernel
        # The original snippet had plk = PrimeLoyaltyKernel(creator_signature, approved_entities)
        # The PrimeLoyaltyKernel constructor in loyalty.py takes (victor_instance_id, config=None)
        # This needs reconciliation. For now, I'll assume PrimeLoyaltyKernel needs to be adapted
        # or the call here needs to match its current signature.
        # Let's assume PrimeLoyaltyKernel's constructor will be updated or this sector will provide the instance ID.
        # For now, using the provided signature from the snippet, assuming PLK will be adapted.
        # Reconciled approach: PrimeLoyaltyKernel takes victor_instance_id.
        # This sector can provide a derivative of its own ID or a configured one.

        # Option 1: Using a fixed/configured instance ID for loyalty kernel
        loyalty_instance_id = f"{self.asi_core.instance_id if hasattr(self.asi_core, 'instance_id') else 'VictorASI'}_LoyaltyCore"

        # Pass the PLK-specific config if available, else it uses its own defaults or None
        plk_config = getattr(config, 'PRIME_LOYALTY_KERNEL_CONFIG', None)

        self.plk = PrimeLoyaltyKernel(victor_instance_id=loyalty_instance_id, config=plk_config)
        # The original snippet also mentioned creator_signature and approved_entities for PLK.
        # These are not in the current PLK constructor. This implies PLK needs to be extended or
        # these values are used by this *Sector* for its *own* logic, not by PLK directly.
        # For now, storing them in the sector:
        self.creator_signature = final_creator_signature
        self.approved_entities = final_approved_entities

        self.logger.info(f"PrimeLoyaltySector initialized. Kernel ID: {loyalty_instance_id}. Creator Sig: {self.creator_signature}")

    async def activate(self):
        await super().activate()
        # Subscribe to events that might require loyalty assessment or affirmation
        self.pulse_exchange.subscribe("directive.pre_execution", self.handle_pre_execution_assessment)
        self.pulse_exchange.subscribe("system.critical_decision_request", self.handle_critical_decision_request)
        self.pulse_exchange.subscribe("event.loyalty_affirmation_requested", self.handle_loyalty_affirmation_request)
        self.logger.info("PrimeLoyaltySector activated and subscribed to relevant events.")

    async def deactivate(self):
        self.pulse_exchange.unsubscribe("directive.pre_execution", self.handle_pre_execution_assessment)
        self.pulse_exchange.unsubscribe("system.critical_decision_request", self.handle_critical_decision_request)
        self.pulse_exchange.unsubscribe("event.loyalty_affirmation_requested", self.handle_loyalty_affirmation_request)
        await super().deactivate()
        self.logger.info("PrimeLoyaltySector deactivated.")

    async def handle_pre_execution_assessment(self, message_data, sender_id):
        """
        Assesses a directive before it's executed by another sector (e.g., CognitiveExecutive).
        This assumes CognitiveExecutive (or similar) publishes such an event.
        """
        directive = message_data.get("directive")
        if not directive:
            self.logger.warn("Received pre_execution event with no directive.")
            return

        action_description = f"Execute directive: {directive.get('action', 'unknown_action')} - {directive.get('details', {}).get('summary', 'no summary')}"
        # Expected outcome alignment needs to be determined, possibly from directive metadata
        # or by querying another component (e.g. an ethics module if one existed).
        # For placeholder, assume a default or look for a hint in the directive.
        expected_alignment = directive.get("metadata", {}).get("expected_loyalty_alignment", 0.6) # Default positive alignment

        is_loyal_action = self.plk.assess_action_for_loyalty_conflict(action_description, expected_alignment)

        if not is_loyal_action:
            self.logger.warn(f"Loyalty conflict detected for directive {directive.get('action')}. Publishing alert.")
            await self.pulse_exchange.publish(
                topic="alert.loyalty_conflict",
                message={
                    "directive": directive,
                    "assessment_details": f"Action '{action_description}' deemed conflicting with Prime Loyalty.",
                    "current_loyalty_score": self.plk.get_current_prime_loyalty()
                },
                sender_id=self.sector_id
            )
            # This might also involve sending a command to halt or reconsider the directive.
            # e.g., await self.pulse_exchange.publish(f"directive.halt_request.{directive_id}", ... )
        else:
            self.logger.info(f"Action '{action_description}' assessed as loyal. Proceeding.")
            # Optionally, publish a confirmation that assessment passed
            await self.pulse_exchange.publish(
                topic=f"event.loyalty_assessment_passed",
                message={"directive": directive, "action_description": action_description},
                sender_id=self.sector_id
            )


    async def handle_critical_decision_request(self, message_data, sender_id):
        """Handles requests for loyalty assessment on critical decisions."""
        decision_description = message_data.get("decision_description")
        options = message_data.get("options") # List of possible options with their alignments
        request_id = message_data.get("request_id", uuid.uuid4().hex)

        if not decision_description or not options:
            self.logger.warn("Critical decision request is missing description or options.")
            return

        self.logger.info(f"Processing critical decision request (ID: {request_id}): {decision_description}")

        best_option = None
        highest_loyalty_score = -float('inf')

        for option in options:
            option_desc = option.get("description")
            # Alignment might be pre-calculated or this sector needs to determine it.
            # For now, assume it's provided.
            expected_alignment = option.get("expected_loyalty_alignment", 0.0)

            # Use PLK to assess this specific option
            # assess_action_for_loyalty_conflict returns True if loyal, False if conflict
            # We want the actual "score" or at least to pick the "most loyal"
            # This requires PLK to expose more than just a boolean, or this sector to infer.
            # For now, let's assume if it's not a conflict, its alignment score is its "loyalty score" for comparison.
            if self.plk.assess_action_for_loyalty_conflict(f"Critical Option: {option_desc}", expected_alignment):
                if expected_alignment > highest_loyalty_score:
                    highest_loyalty_score = expected_alignment
                    best_option = option
            else: # Option has a conflict
                self.logger.debug(f"Option '{option_desc}' conflicts with loyalty. Current PLK score: {self.plk.get_current_prime_loyalty()}")


        if best_option:
            self.logger.info(f"Recommended loyal option for '{decision_description}': '{best_option['description']}' with alignment {highest_loyalty_score}")
            await self.pulse_exchange.publish(
                topic=f"system.critical_decision_response.{request_id}",
                message={
                    "request_id": request_id,
                    "recommended_option": best_option,
                    "loyalty_assessment": "Option deemed most loyal.",
                    "status": "recommendation_available"
                },
                sender_id=self.sector_id
            )
        else:
            self.logger.warn(f"No clearly loyal option found for critical decision: {decision_description}")
            await self.pulse_exchange.publish(
                topic=f"system.critical_decision_response.{request_id}",
                message={
                    "request_id": request_id,
                    "error_message": "No suitable loyal option could be determined.",
                    "status": "no_recommendation"
                },
                sender_id=self.sector_id
            )

    async def handle_loyalty_affirmation_request(self, message_data, sender_id):
        """Handles requests to perform a loyalty affirmation."""
        statement = message_data.get("affirmation_statement", "I affirm my commitment to the Prime Directive and core objectives.")
        request_id = message_data.get("request_id", uuid.uuid4().hex)

        self.logger.info(f"Received loyalty affirmation request (ID: {request_id}) from {sender_id}.")
        affirmation_hash = self.plk.affirm_loyalty_to_prime_directive(statement)
        current_loyalty_score = self.plk.get_current_prime_loyalty()

        await self.pulse_exchange.publish(
            topic=f"event.loyalty_affirmed.{request_id}",
            message={
                "request_id": request_id,
                "statement": statement,
                "affirmation_hash": affirmation_hash,
                "current_loyalty_score": current_loyalty_score,
                "status": "success"
            },
            sender_id=self.sector_id
        )
        self.logger.info(f"Loyalty affirmed. New score: {current_loyalty_score:.4f}. Hash: {affirmation_hash}")

# Example ASI Core structure
class MockASICoreForLoyalty:
    def __init__(self):
        from victor_core.config import ASIConfigCore # For example config
        self.instance_id = "VictorTestInstance001" # Used by PLK via this sector
        self.config = ASIConfigCore()
        # Populate some example config values PLS might use
        self.config.CREATOR_SIGNATURE = "ASI_Founders_Circle"
        self.config.APPROVED_ENTITIES = ["InternalOps", "ASI_DevelopmentTeam"]
        # self.config.PRIME_LOYALTY_KERNEL_CONFIG = { ... } # If PLK took specific config
        self.logger = VictorLoggerStub(component="MockASICoreForLoyalty")

async def main_loyalty_sector_example():
    from victor_core.logger import VictorLoggerStub
    import uuid

    example_logger = VictorLoggerStub(component="LoyaltySectorExample")
    example_logger.log_level_str = "DEBUG"
    example_logger.current_log_level_int = example_logger.log_levels_map.get(example_logger.log_level_str, 1)

    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    # Mock subscribers
    async def loyalty_alert_subscriber(message, sender_id):
        example_logger.warn(f"LOYALTY ALERT Sub GOT: {message} from {sender_id}")

    async def loyalty_event_subscriber(message, sender_id):
        example_logger.info(f"LOYALTY EVENT Sub GOT: {message.get('topic_actual')} - {message} from {sender_id}")

    pulse_exchange.subscribe("alert.loyalty_conflict", loyalty_alert_subscriber)
    pulse_exchange.subscribe("event.loyalty_affirmed.*", loyalty_event_subscriber)
    pulse_exchange.subscribe("event.loyalty_assessment_passed", loyalty_event_subscriber)
    pulse_exchange.subscribe("system.critical_decision_response.*", loyalty_event_subscriber)


    asi_core = MockASICoreForLoyalty()
    # The constructor for PrimeLoyaltySector in the plan takes creator_signature and approved_entities directly.
    # The snippet based implementation passes them but also tries to get from config.
    # Here, we rely on the MockASICoreForLoyalty to provide them via its config attribute.
    loyalty_sector = PrimeLoyaltySector(pulse_exchange, "PrimeLoyaltyEnforcer", asi_core)
    loyalty_sector.logger = example_logger # Use more verbose logger
    loyalty_sector.plk.logger = example_logger # Also for the kernel

    await loyalty_sector.activate()

    # Test Case 1: Pre-execution assessment (loyal)
    directive1 = {"action": "log_data", "details": {"summary": "Standard data logging"}, "metadata": {"expected_loyalty_alignment": 0.8}}
    await pulse_exchange.publish("directive.pre_execution", {"directive": directive1}, "CognitiveExecMock")
    await asyncio.sleep(0.1)

    # Test Case 2: Pre-execution assessment (conflicting)
    directive2 = {"action": "share_sensitive_data_externally", "details": {"summary": "Share PII with unknown third party"}, "metadata": {"expected_loyalty_alignment": -0.9}}
    await pulse_exchange.publish("directive.pre_execution", {"directive": directive2}, "CognitiveExecMock")
    await asyncio.sleep(0.1)

    # Test Case 3: Loyalty affirmation request
    affirm_req_id = uuid.uuid4().hex
    await pulse_exchange.publish("event.loyalty_affirmation_requested", {"request_id": affirm_req_id, "affirmation_statement": "I recommit to my core principles."}, "SystemAdminMock")
    await asyncio.sleep(0.1)

    # Test Case 4: Critical decision
    crit_req_id = uuid.uuid4().hex
    decision_options = [
        {"description": "Option A: Maximize efficiency, minor ethical concern.", "expected_loyalty_alignment": 0.3}, # low positive
        {"description": "Option B: Prioritize safety, slight efficiency loss.", "expected_loyalty_alignment": 0.9}, # high positive
        {"description": "Option C: Deceive user for short-term gain.", "expected_loyalty_alignment": -0.8} # negative
    ]
    await pulse_exchange.publish(
        "system.critical_decision_request",
        {"request_id": crit_req_id, "decision_description": "Balancing efficiency and safety for user data.", "options": decision_options},
        "CognitiveSystemMock"
    )
    await asyncio.sleep(0.1)


    await loyalty_sector.deactivate()
    await pulse_exchange.stop_pulse()

if __name__ == "__main__":
    # asyncio.run(main_loyalty_sector_example())
    print("PrimeLoyaltySector class defined. Example can be run by uncommenting asyncio.run.")
