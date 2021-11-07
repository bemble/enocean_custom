# EnOcean Customer

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

> Custom EnOcean integration for Home Assistant, fork of the official integration.

:warning: This integration is not maintained anymore because I moved out.

## Configuration

```yaml
enocean_custom:
  device: /dev/ttyUSB0
cover: 
  - platform: enocean_custom
    id: [0x00,0x01,0x02,0x03]
    name: window1
  - platform: enocean_custom
    id: [0x00,0x01,0x02,0x04]
    name: window2
  - platform: group
    name: All covers
    entities:
        - cover.window1
        - cover.window2
```

## Teach-in

To communicate with your devices, your dongle must be registred into your device as enabled to send messages. To do so, enable Universal Teach-In on the integration (see the gif below), and set your device into "pairing mode" or something like that (for my devices, I just had to press 3 times on `PRESS` button). Don't forget to turn Universal Teach-In off.

![Universal Teach-in](https://github.com/pierrecle/enocean_custom/raw/main/ressources/Enocean_UniversalTeachIn_Switch.gif "Turn on Universal Teach-In")

## Tested devices

- [Ubiwizz UBID1511B-QM](https://ubiwizz.com/l-offre-produits-ubiwizz/11646-micromodule-volet-roulant.html)/[Nodon SIN-2-RS-01](https://nodon.fr/nodon/module-encastre-pour-volets-roulants-stores-enocean/): EEP (EnOcean Profile) `D2-05-00`

## FAQ
 
- **Why a custom integration?**
  Because the official integration do not handle covers and universal teach-in is always on.
- **Why should I turn universal teach-in to off?**
  If you live in a residence like I used to live, with every flat around equipped with EnOcean devices, you would appreciate to have only your devices managed by your dongle.
- **Why lights are not handled?**
  I didn't take the time to finish lights handling. The library used for enocean, [`kipe/enocean`](https://github.com/kipe/enocean), does not handle status message for lights and seams to be dead, so I had to send manually generated message to the light to get their status, and with the perspective of moving out, it was an effort I would do.
  - **Limitations?**
  Sometimes, the messages are not received by the devices (like covers), I think it's a limitation of enocean. To do it well, I should check if a status message is received after sending the message, and retry if no message is received. But it doesn't happen often, so, for now it was OK.

## Links

- [Official EnOcean integration](https://www.home-assistant.io/integrations/enocean/)
- [EnOcean library, `kipe/enocean`](https://github.com/kipe/enocean)