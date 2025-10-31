# Dummy plugin: dummy_plugin
LOGGER = None
ASI_CORE = None
def initialize_plugin(asi_core_ref, logger_instance):
    global LOGGER, ASI_CORE
    LOGGER = logger_instance
    ASI_CORE = asi_core_ref
    LOGGER.info('dummy_plugin initialized by ModularPluginCortex.')

def sample_function():
    LOGGER.info('dummy_plugin.sample_function called.')
    return 'Dummy plugin says hello!'
