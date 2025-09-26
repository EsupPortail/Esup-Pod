---
layout: default
version: 4.x
lang: en
---

# Using maintenance mode

Since version 2.7.0, Pod has included a maintenance mode that is very useful when updating the platform. It allows you to disable the addition of videos (and therefore the launch of encodings) while still keeping the platform accessible for viewing.

This way, you can let encodings in progress finish before launching a Pod upgrade.

> 💡Information: unlike other Pod features, maintenance mode is activated by the administration instead of a setting (this allows you to activate it without having to restart the platform).

To activate and customise maintenance mode, go to the ‘Configuration’ section of the administration panel:

- The `maintenance_mode` parameter activates maintenance mode; you must set it to ‘1’ to activate it.
- The `maintenance_text_short` parameter is the text that will be displayed in the navigation bar.
- The `maintenance_text_welcome` parameter is the text displayed on the application’s home page in a banner.
- The `maintenance_text_disabled` parameter is the text displayed on the page to which a user is redirected when attempting to access a feature that is under maintenance.
