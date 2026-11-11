# Printers and cameras (planned)

Nothing here is built yet. This is the plan for how Gantrel will connect to 3D printers and their cameras.

## Safety rules

- **A print never starts without the user's confirm.** Start needs a confirm token that only the confirm sheet in the app creates, showing the file, printer, material and time. No agent, skill or script can start a print.
- **Emergency stop is always visible and works in one press.**
- **Pause needs no confirm**, because it's a safe action. Resume does.
- Pairing credentials live in the OS keychain, never in plain config.
- Gantrel talks to printers on the local network. Cloud services (PrusaConnect, Bambu Cloud, Creality Cloud) come after v0 and only as an opt-in.

## Adapter contract

Every printer type is an adapter that implements the same calls: discover, pair, status stream, upload, start (with confirm token), pause, resume, cancel, emergency stop, camera streams, and errors. One contract test suite runs against a fake printer for every adapter, and against real printers on the "planned first" list in [SUPPORTED.md](../SUPPORTED.md).

## Planned adapters

| Adapter | How it talks | License note | Build |
|---|---|---|---|
| Klipper with [Moonraker](https://github.com/Arksine/moonraker) | HTTP and WebSocket API | Moonraker and Klipper are GPL-3.0; Gantrel only calls the API. | 5 |
| [OctoPrint](https://github.com/OctoPrint/OctoPrint) | REST API with an app key the user approves in OctoPrint | AGPL-3.0; API only. | 6 |
| [PrusaLink](https://github.com/prusa3d/Prusa-Link) | Local API with the printer's API key | GPL-3.0; API only. PrusaConnect is cloud, after v0. | 6 |
| Bambu Lab, LAN mode | MQTT over TLS (port 8883) with the access code, FTPS upload, camera stream | Protocol references: [ha-bambulab](https://github.com/greghesp/ha-bambulab) (MIT), [bambulabs_api](https://github.com/acse-ci223/bambulabs_api) (MIT). Newer firmware needs LAN-only mode with Developer Mode on for third-party control; the adapter checks and explains. | 7 |
| Creality stock firmware (K1, K2, Ender-3 V3, Hi) | Local WebSocket on port 9999 and HTTP upload, the same API Creality Print uses | Not officially documented and may change with firmware. Reference: [crlancli](https://github.com/axellse/crlancli) (MIT). Record the firmware version tested. | 7 |
| Creality K2 Plus, rooted K1 | Moonraker (the K2 Plus ships it behind port 4408) | Uses the Moonraker adapter. Creality publishes its Klipper sources ([K1](https://github.com/CrealityOfficial/K1_Series_Klipper), [K2](https://github.com/CrealityOfficial/K2_Series_Klipper), GPL-3.0). | 7 |
| Elegoo (SDCP) and others | Written by an agent from the device's docs (see below) | Reference: [elegoo-homeassistant](https://github.com/danielcherubini/elegoo-homeassistant) (MIT). | 9 |

Slicing uses the OrcaSlicer, PrusaSlicer or Creality Print command line (all AGPL-3.0, run as separate programs).

## Cameras

| Part | License | Use |
|---|---|---|
| [go2rtc](https://github.com/AlexxIT/go2rtc) | MIT | Turns MJPEG, RTSP and WebRTC streams, including Bambu's, into one low-latency stream in the app. |
| [crowsnest](https://github.com/mainsail-crew/crowsnest), [moonraker-timelapse](https://github.com/mainsail-crew/moonraker-timelapse) | GPL-3.0 | Run on Klipper printers; Gantrel only reads their streams and files. |
| FFmpeg | LGPL-2.1 or GPL | Builds timelapses for printers that don't. |
| [Obico](https://github.com/TheSpaghettiDetective/obico-server) | AGPL-3.0 | Optional local failure detection that pauses the print. Run unmodified as its own service. |

## Agent-written adapters

An agent can write a new adapter by reading a device's docs or API reference. Before it is used:

1. It runs in its own sandboxed process that can reach only the device's address and its own folder (bubblewrap on Linux, sandbox-exec on macOS).
2. It must pass the contract tests against a fake device built from the docs, then a read-only status check against the real device.
3. The user sees the device, the addresses it can reach, the test results and the code, and approves or rejects it.
4. Gantrel stores the approved adapter's hash. Any change disables it until the user approves again.
5. The confirm-to-start rule still applies; an approved adapter can't start a print on its own.
