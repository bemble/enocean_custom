"""Representation of an EnOcean dongle."""
import glob
import logging
from os.path import basename, normpath

from homeassistant.helpers.entity import ToggleEntity
from enocean.communicators import SerialCommunicator
from enocean.protocol.packet import RadioPacket, UTETeachInPacket
import serial

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import SIGNAL_RECEIVE_MESSAGE, SIGNAL_SEND_MESSAGE

_LOGGER = logging.getLogger(__name__)


class EnOceanDongle:
    """Representation of an EnOcean dongle.

    The dongle is responsible for receiving the ENOcean frames,
    creating devices if needed, and dispatching messages to platforms.
    """

    def __init__(self, hass, serial_path):
        """Initialize the EnOcean dongle."""

        # TODO: remove when https://github.com/kipe/enocean/pull/118 is accepted
        tmp_communicator = SerialCommunicator(port=serial_path)
        tmp_communicator.start()
        self._base_id = tmp_communicator.base_id
        if tmp_communicator.is_alive():
            tmp_communicator.stop()

        self._communicator = SerialCommunicator(
            port=serial_path, callback=self.callback
        )
        self._communicator.base_id = self._base_id
        self._communicator.teach_in = False
        self.serial_path = serial_path
        self.identifier = basename(normpath(serial_path))
        self.hass = hass
        self.dispatcher_disconnect_handle = None
        self._teach_in = False

    async def async_setup(self):
        """Finish the setup of the bridge and supported platforms."""
        self._communicator.start()
        self.dispatcher_disconnect_handle = async_dispatcher_connect(
            self.hass, SIGNAL_SEND_MESSAGE, self._send_message_callback
        )

    def unload(self):
        """Disconnect callbacks established at init time."""
        if self.dispatcher_disconnect_handle:
            self.dispatcher_disconnect_handle()
            self.dispatcher_disconnect_handle = None

    def _send_message_callback(self, command):
        """Send a command through the EnOcean dongle."""
        self._communicator.send(command)

    def callback(self, packet):
        """Handle EnOcean device's callback.

        This is the callback function called by python-enocan whenever there
        is an incoming packet.
        """

        # TODO: log ute
        if isinstance(packet, UTETeachInPacket):
            if self._communicator.teach_in:
                _LOGGER.debug("Handled universal teach-in packet received (%s)", packet)
                response_packet = packet.create_response_packet(self._base_id)
                _LOGGER.debug("Sending reply to universal teach-in (%s)", response_packet)
                self._communicator.send(response_packet)
            else:
                _LOGGER.debug("Ignored teach-in packet received (%s)", packet)

        if isinstance(packet, RadioPacket):
            _LOGGER.debug("Received radio packet: %s", packet)
            self.hass.helpers.dispatcher.dispatcher_send(SIGNAL_RECEIVE_MESSAGE, packet)

    @property
    def base_id(self):
        return self._base_id

    @property
    def teach_in(self):
        return self._teach_in

    def enable_teach_in(self):
        _LOGGER.debug("Automatic teach-in enabled")
        self._teach_in = True

    def disable_teach_in(self):
        _LOGGER.debug("Automatic teach-in disabled")
        self._teach_in = False


def detect():
    """Return a list of candidate paths for USB ENOcean dongles.

    This method is currently a bit simplistic, it may need to be
    improved to support more configurations and OS.
    """
    globs_to_test = ["/dev/tty*FTOA2PV*", "/dev/serial/by-id/*EnOcean*"]
    found_paths = []
    for current_glob in globs_to_test:
        found_paths.extend(glob.glob(current_glob))

    return found_paths


def validate_path(path: str):
    """Return True if the provided path points to a valid serial port, False otherwise."""
    try:
        # Creating the serial communicator will raise an exception
        # if it cannot connect
        SerialCommunicator(port=path)
        return True
    except serial.SerialException as exception:
        _LOGGER.warning("Dongle path %s is invalid: %s", path, str(exception))
        return False