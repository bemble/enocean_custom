"""Constants for the ENOcean integration."""
import logging

DOMAIN = "enocean_custom"
DATA_ENOCEAN = "enocean_custom"
ENOCEAN_DONGLE = "dongle"

ERROR_INVALID_DONGLE_PATH = "invalid_dongle_path"

SIGNAL_RECEIVE_MESSAGE = "enocean.receive_message"
SIGNAL_SEND_MESSAGE = "enocean.send_message"

LOGGER = logging.getLogger(__package__)

PLATFORMS = ["light", "binary_sensor", "sensor", "switch", "cover"]
