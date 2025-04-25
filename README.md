# 360 / Qihoo / Botslab 360 Vacuum Robot Home Assistant Integration

This is a custom component for Home Assistant to integrate with 360 vacuum robots.
You will need this proxy server running for this integration to work: ...

## Installation

### Using HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=cn360-homeassistant&owner=cavefire)

1. Click the link above to open the integration in HACS.
2. Install the integration.

### Manual Installation

1. Clone or download this repository.
2. Copy the `custom_components/cn360` directory to your Home Assistant `config` directory.
3. Restart Home Assistant.

## Setup

1. Go to "Configuration" -> "Devices & Services" -> "Add Device" -> "CN360".
2. Enter the host and port of your proxy and click "Add"

## Proxy

As far as I could figure out, there is no native way to control the vacuum robot fully locally. Since the servers of 360 (Qihoo 360 / Botslab 360 and so many more names...) 
are mostly located in China, controlling the robots sends the traffic halfway around the world for me.

Because of this reason, I created a proxy (link here...), which acts as a Man in the Middle, to capture the events from the robot and send commands to it. **The proxy is needed for this
integration to work!**

## Features

This is the list of features implemented in the integration. Non-marked features are not yet implemented. Feel free to do so!

- [x] Start cleaning
- [x] Pause cleaning
- [x] Back to dock / Charging
- [x] Battery status
- [x] Current map view with postion
- [x] General settings
- [x] Reboot
- [x] Locate  
- [ ] Path on map
- [ ] Switch between maps
- [ ] Upload custom sound packs
- [ ] Mop and / or vacuum selection
- [ ] Water amount
- [ ] Cleaning amount
- [ ] Cleaning schedule

### Supported Devices

- [x] S9

I only have this one to test.

If you have a device that is not listed here, please open an issue or a pull request.
These devices only work with the features that are marked as completed above.
**If a feature is missing on your device, please open an issue.**

## Contributing
This project is a work in progress, and contributions are welcome!
If you encounter issues, have feature requests, or want to contribute, feel free to submit a pull request or open an issue.

If you like this project, consider supporting me 
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/cavefire)


## Disclaimer
This project is not affiliated with Qihoo 360 Technology Co. Ltd. The API and all functions are reverse-engineered and may break at any time. Use at your own risk.

**To the Qihoo 360 legal team:**
I found out all the functions with my own device and did not use any copyright-protected data. This activity is legally protected in Germany.
However, if there are any concerns, we will surely find a way to mitigate them together.

## License
This project is licensed under GNU GPLv3 - see the [LICENSE](LICENSE) file for details.
