# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class LaserCutterPlugin(octoprint.plugin.StartupPlugin,
						octoprint.plugin.TemplatePlugin,
						octoprint.plugin.SettingsPlugin,
						octoprint.plugin.AssetPlugin):
    def on_after_startup(self):
        self._logger.info("Laser Cutter")

	def get_settings_defaults(self):
		return dict(
			test_setting="foo",
			test_value=42,
			sub=dict(
				test_flag=true
			)
		)

	def get_template_configs(self):
		return[
			dict(type="navbar", custom_bindings=False),
			dict(type="settings", custom_bindings=False)
		]

	def get_assets(self):
		return dict(
			js=["js/lasercutter.js"]
		)

__plugin_name__ = "Laser Cutter"
__plugin_implementation__ = LaserCutterPlugin()
