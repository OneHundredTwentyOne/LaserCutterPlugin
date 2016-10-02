# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from svgConverter import svg2gcode


class LaserCutterPlugin(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin,
                        octoprint.plugin.AssetPlugin):
    def on_after_startup(self):
        self._logger.info("Laser Cutter (more: %s)" % self._settings.get(["url"]))

    def get_settings_defaults(self):
        return dict(url="https://en.wikipedia.org/wiki/Hello_world")

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False),
            dict(type="tab", custom_bindings=False)
        ]

    def get_assets(self):
        return dict(
            js=["js/lasercutter.js"],
            css=["css/lasercutter.css"],
            less=["less/lasercutter.less"]
        )


__plugin_name__ = "Laser Cutter"
__plugin_implementation__ = LaserCutterPlugin()
