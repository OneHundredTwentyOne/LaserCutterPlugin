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
