# coding=utf-8
from __future__ import absolute_import

#imports necessary from octoprint
import octoprint.plugin
import octoprint.util
import octoprint.slicing
import octoprint.settings

#other imports
import logging
import logging.handlers
import os
import flask
import math

#imports Peter's SVG converter
import svgConverter as svg_converter


class LaserCutterPlugin(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin,
                        octoprint.plugin.AssetPlugin,
						octoprint.plugin.BlueprintPlugin,
						octoprint.plugin.SlicerPlugin):

	def __init__(self):
		print "Initialising OctoPrint LaserCutter plugin"
		self._slicing_commands = dict()
		self._cancelled_jobs = []

	def get_template_vars(self):
		return dict(
			homepage=__plugin_url__
		)

	def on_startup(self):
		print "On STARTUP"

	def get_slicer_properties(self):
		return dict(
			type="lasercutter",
			name="Laser Cutter",
			same_device = True,
			progress_report = True,
			source_file_types= ["svg"],
			destination_extensions = ["gco", "gcode", "g"]
		)

	def get_slicer_default_profile(self):
		path = self._settings.get(["default_profile"])
		if not path:
			path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "profiles", "default.profile.yaml")
		return self.get_slicer_profile(path)

	def get_slicer_profile(self, path):
		profile_dict = self._load_profile(path)
		display_name = None
		description = None
		if "_display_name" in profile_dict:
			display_name = profile_dict["_display_name"]
			del profile_dict["_display_name"]
		if "_description" in profile_dict:
			description = profile_dict["_description"]
			del profile_dict["_description"]
		properties = self.get_slicer_properties()
		return octoprint.slicing.SlicingProfile(properties["type"], "unknown", profile_dict, display_name = display_name, description = description)

	def do_slice(self, model_path, printer_profile, machinecode_path = None, profile_path = None,
				 position = None, on_progress = None, on_progress_args = None, on_progress_kwargs = None):
		pass

	def is_slicer_configured(self):
		print "Set to true so it should always be enabled"
		return True

	@property
	def slicing_enabled(self):
		return True

	def get_assets(self):
		return{
			"js": ["js/lasercutter.js"],
			"less": ["less/lasercutter.less"],
			"css": ["css/lasercutter.css"]
		}

__plugin_name__ = "Laser Cutter"
__plugin_implementation__ = LaserCutterPlugin()
__plugin_url__ = "https://github.com/thepangman/OctoPrint-LaserCutter.git"
