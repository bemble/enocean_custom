"""Support for EnOcean switches."""
import voluptuous as vol
import logging

from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import CONF_ID, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import ToggleEntity

from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import RORG

from .device import EnOceanEntity
from .const import DATA_ENOCEAN, ENOCEAN_DONGLE

CONF_SENDER_ID = "sender_id"
CONF_CHANNEL = "channel"
CONF_RORG = "rorg"
CONF_RORG_FUNC = "rorg_func"
CONF_RORG_TYPE = "rorg_type"
DEFAULT_NAME = "EnOcean Switch"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SENDER_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_CHANNEL, default=0): cv.positive_int,
        vol.Optional(CONF_RORG, default=RORG.VLD): cv.positive_int,
        vol.Optional(CONF_RORG_FUNC, default=0x01): cv.positive_int,
        vol.Optional(CONF_RORG_TYPE, default=0x01): cv.positive_int
    }
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the EnOcean switch platform."""
    channel = config.get(CONF_CHANNEL)
    dev_id = config.get(CONF_ID)
    sender_id = config.get(CONF_SENDER_ID)
    rorg = config.get(CONF_RORG)
    rorg_func = config.get(CONF_RORG_FUNC)
    rorg_type = config.get(CONF_RORG_TYPE)
    dev_name = config.get(CONF_NAME)

    add_entities([EnOceanSwitch(sender_id, rorg, rorg_func, rorg_type, dev_id, dev_name, channel)])

async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    async_add_entities([EnOceanDongleTeachInSwitch()])


class EnOceanSwitch(EnOceanEntity, ToggleEntity):
    """Representation of an EnOcean switch device."""

    def __init__(self, sender_id, rorg, rorg_func, rorg_type, dev_id, dev_name, channel):
        """Initialize the EnOcean switch device."""
        super().__init__(dev_id, dev_name)
        self._sender_id = sender_id
        self._rorg = rorg
        self._rorg_func = rorg_func
        self._rorg_type = rorg_type
        self._on_state = False
        self.channel = channel

    @property
    def unique_id(self):
        """Return a unique ID."""
        return (super().unique_id + "_" + str(self.channel)).lower()

    @property
    def is_on(self):
        """Return whether the switch is on or off."""
        return self._on_state

    @property
    def name(self):
        """Return the device name."""
        return self.dev_name

    @property
    def sender_id(self):
        if self._sender_id != None:
            return self._sender_id
        return self.hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE].base_id

    async def async_added_to_hass(self):
        """To restore state, ask switch status."""
        await super().async_added_to_hass()
        #self.ask_switch_status()

    def update(self):
        """Ask switch status."""
        #self.ask_switch_status()

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        self.send_packet(RadioPacket.create(rorg=self._rorg, rorg_func=self._rorg_func, rorg_type=self._rorg_type, destination=self.dev_id, sender=self.sender_id, command=1, IO=self.channel & 0xFF, OV=100))

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        self.send_packet(RadioPacket.create(rorg=self._rorg, rorg_func=self._rorg_func, rorg_type=self._rorg_type, destination=self.dev_id, sender=self.sender_id, command=1, IO=self.channel & 0xFF, OV=0))

    def ask_switch_status(self):
        self.send_packet(RadioPacket.create(rorg=self._rorg, rorg_func=self._rorg_func, rorg_type=self._rorg_type, destination=self.dev_id, sender=self.sender_id, command=3, IO=self.channel & 0xFF))

    def value_changed(self, packet):
        """Update the internal state of the switch."""
        if isinstance(packet, RadioPacket) and packet.sender == self.dev_id and packet.rorg == RORG.VLD:
            packet.select_eep(self._rorg_func, self._rorg_type)
            packet.parse_eep()
            raw_io = packet.parsed['IO']['raw_value']
            if io == self.channel:
                raw_value = packet.parsed['OV']['raw_value']
                if raw_value > 100:
                    _LOGGER.debug("/!\ Unkown position received for %s (%d)", self.dev_name, raw_value)
                    self._current_cover_position = None
                else:
                    _LOGGER.debug("New position received for %s: %d", self.dev_name, raw_value)
                    self._on_state = raw_value > 0

class EnOceanDongleTeachInSwitch(ToggleEntity):
    def __init__(self):
        super().__init__()

    @property
    def unique_id(self):
        """Return a unique ID."""
        return "enocean_universale_teach_in"

    @property
    def name(self):
        return "Enocean Universal Teach-in"

    def turn_on(self, **kwargs):
        self.hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE].enable_teach_in()

    def turn_off(self, **kwargs):
        self.hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE].disable_teach_in()

    @property
    def is_on(self):
        return self.hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE].teach_in