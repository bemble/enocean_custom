"""Support for EnOcean covers."""
import voluptuous as vol
import logging
import time

from homeassistant.components.cover import (
    ATTR_POSITION,
    SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_STOP, SUPPORT_SET_POSITION,
    PLATFORM_SCHEMA,
    CoverEntity,
)
from homeassistant.const import CONF_ID, CONF_NAME, CONF_DEVICE_CLASS
import homeassistant.helpers.config_validation as cv

from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import RORG

from .const import DATA_ENOCEAN, ENOCEAN_DONGLE
from .device import EnOceanEntity

CONF_RORG = "rorg"
CONF_RORG_FUNC = "rorg_func"
CONF_RORG_TYPE = "rorg_type"
DEFAULT_NAME = "EnOcean Cover"

# TODO: add doc to appair, to calibrate
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_RORG, default=RORG.VLD): cv.positive_int,
        vol.Optional(CONF_RORG_FUNC, default=0x05): cv.positive_int,
        vol.Optional(CONF_RORG_TYPE, default=0x00): cv.positive_int
    }
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the EnOcean cover platform."""
    dev_id = config.get(CONF_ID)
    dev_name = config.get(CONF_NAME)
    rorg = config.get(CONF_RORG)
    rorg_func = config.get(CONF_RORG_FUNC)
    rorg_type = config.get(CONF_RORG_TYPE)

    add_entities([EnOceanCover(rorg, rorg_func, rorg_type, dev_id, dev_name)])

async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    return True


class EnOceanCover(EnOceanEntity, CoverEntity):
    """Representation of an EnOcean switch device."""

    def __init__(self, rorg, rorg_func, rorg_type, dev_id, dev_name):
        """Initialize the EnOcean switch device."""
        super().__init__(dev_id, dev_name)
        self._rorg = rorg
        self._rorg_func = rorg_func
        self._rorg_type = rorg_type
        self._previous_cover_position = None
        self._current_cover_position = None
        self._supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP |  SUPPORT_SET_POSITION

    async def async_added_to_hass(self):
        """To restore state, ask cover position."""
        await super().async_added_to_hass()
        self.ask_cover_position()

    def update(self):
        """Ask cover position."""
        self.ask_cover_position()

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    @property
    def name(self):
        """Return the device name."""
        return self.dev_name

    @property
    def current_cover_position(self):
        return self._current_cover_position

    @property
    def is_opening(self):
        if self._current_cover_position == None or self._previous_cover_position == None:
            return None
        if self._previous_cover_position == self._current_cover_position:
            return None
        return self._previous_cover_position < self._current_cover_position

    @property
    def is_closing(self):
        if self._current_cover_position == None or self._previous_cover_position == None:
            return None
        if self._previous_cover_position == self._current_cover_position:
            return None
        return self._previous_cover_position > self._current_cover_position

    @property
    def is_closed(self):
        if self._current_cover_position == None:
            return None
        return self._current_cover_position == 0

    @property
    def sender_id(self):
        return self.hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE].base_id

    def open_cover(self, **kwargs):
        kwargs[ATTR_POSITION] = 100
        self.set_cover_position(**kwargs)

    def close_cover(self, **kwargs):
        kwargs[ATTR_POSITION] = 0
        self.set_cover_position(**kwargs)

    def stop_cover(self, **kwargs):
        self._current_cover_position = 100
        self.send_packet(RadioPacket.create(rorg=self._rorg, rorg_func=self._rorg_func, rorg_type=self._rorg_type, destination=self.dev_id, sender=self.sender_id, command=2))

    def set_cover_position(self, **kwargs):
        if ATTR_POSITION in kwargs:
            position = 100 - kwargs[ATTR_POSITION]
            self.send_packet(RadioPacket.create(rorg=self._rorg, rorg_func=self._rorg_func, rorg_type=self._rorg_type, destination=self.dev_id, sender=self.sender_id, command=1, POS=position))
    
    def ask_cover_position(self):
        self.send_packet(RadioPacket.create(rorg=self._rorg, rorg_func=self._rorg_func, rorg_type=self._rorg_type, destination=self.dev_id, sender=self.sender_id, command=3))

    def value_changed(self, packet):
        """Update the internal state of the switch."""
        if isinstance(packet, RadioPacket) and packet.sender == self.dev_id and packet.rorg == RORG.VLD:
            packet.select_eep(self._rorg_func, self._rorg_type)
            packet.parse_eep()
            raw_pos = packet.parsed['POS']['raw_value']
            if raw_pos == 127:
                _LOGGER.debug("/!\ Unkown position received for %s (%d)", self.dev_name, raw_pos)
                self._current_cover_position = None
            else:
                _LOGGER.debug("New position received for %s: %d", self.dev_name, (100 - raw_pos))
                self._previous_cover_position = self._current_cover_position
                self._current_cover_position = 100 - raw_pos

