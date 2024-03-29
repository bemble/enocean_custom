"""Support for EnOcean devices."""
import voluptuous as vol
import logging

from homeassistant import config_entries, core
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_DEVICE
import homeassistant.helpers.config_validation as cv

from .const import DATA_ENOCEAN, DOMAIN, ENOCEAN_DONGLE,PLATFORMS
from .dongle import EnOceanDongle

CONF_TEACH_IN = "teach_in"

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.string})}, extra=vol.ALLOW_EXTRA
)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the EnOcean component."""
    
    # support for text-based configuration (legacy)
    if DOMAIN not in config:
        return True

    if hass.config_entries.async_entries(DOMAIN):
        # We can only have one dongle. If there is already one in the config,
        # there is no need to import the yaml based config.
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
        )
    )

    return True


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry):
    """Set up an EnOcean dongle for the given entry."""

    enocean_data = hass.data.setdefault(DATA_ENOCEAN, {})
    usb_dongle = EnOceanDongle(hass, config_entry.data[CONF_DEVICE])
    await usb_dongle.async_setup()
    enocean_data[ENOCEAN_DONGLE] = usb_dongle

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass, config_entry):
    """Unload ENOcean config entry."""

    enocean_dongle = hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE]
    enocean_dongle.unload()
    hass.data.pop(DATA_ENOCEAN)

    return True
