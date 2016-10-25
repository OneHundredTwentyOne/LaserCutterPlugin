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
		self._logger = logging.getLogger("octoprint.plugins.lasercutter")
		import threading
		self._slicing_commands = dict()
		self._cancelled_jobs = []
		self._job_mutex = threading.Lock()

	def get_template_vars(self):
		return dict(
			homepage=__plugin_url__
		)

	def on_startup(self):
		print "On STARTUP"

	def get_slicer_properties(self):

		print "GET SLICER PROPERTIES FUNCTION"

		return dict(
			type="lasercutter",
			name="Laser Cutter",
			same_device = True,
			progress_report = True,
			source_file_types= ["svg"],
			destination_extensions = ["gco", "gcode", "g"]
		)

	@octoprint.plugin.BlueprintPlugin.route("/import", methods=["POST"])
	def import_laser_profile(self):
		import tempfile
		import datetime

		from octoprint.server import slicingManager

		print "IMPORT PROFILE FUNCTION"

		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		if input_upload_name in flask.request.values and input_upload_path in flask.request.values:
			filename = flask.request.values[input_upload_name]
			try:
				profile_dict = Profile.from_lasercutter_ini(flask.request.values[input_upload_path])
			except Exception as e:
				self._logger.exception("Error while converting the imported profile")
				return flask.make_response("No file included", 400)

		if profile_dict is None:
			self._logger.warn("Could not convert profile, aborting")
			return flask.make_response("Could not convert profile", 400)

		name, _ = os.path.splitext(filename)

		profile_name = name
		profile_display_name = name
		profile_description = "Laser profile"
		profile_allow_overwrite = False

		if "name" in flask.request.values:
			profile_name = flask.request.values["name"]
		if "displayName" in flask.request.values:
			profile_display_name = flask.request.values["displayName"]
		if "description" in flask.request.values:
			profile_description = flask.request.values["Imported from {filename} on {date}".format(filename = filename, 
				date = octoprint.util.get_formatted_datetime(datetime.datetime.now()))]
		if "allowOverwrite" in flask.request.values:
			from octoprint.server.api import valid_boolean_trues
			profile_allow_overwrite = flask.request.values["allowOverwrite"] in valid_boolean_trues

		try:
			slicingManager.save_profile("lasercutter", profile_name, profile_dict,
										allow_overwrite = profile_allow_overwrite, display_name = profile_display_name,
										description = profile_description)
		except octoprint.slicing.ProfileAlreadyExists:
			self._logger.warn("Profile already exists")
			print("Profile")
			return flask.make_response("Profile already exists", 409)

		result = dict(
			resource = flask.url_for("api.slicingGetSlicerProfile", slicer = "lasercutter", name = profile_name,
									 _external = True),
			displayName = profile_display_name,
			description = profile_description
		)	
		r = flask.make_response(flask.jsonify(result), 201)
		r.headers["Location"] = result["resource"]
		return r


	def _load_profile(self, path):
		print "LOAD PROFILE FUNCTION"
		import yaml
		profile_dict = dict()
		with open(path, "r") as f:
			try:
				profile_dict = yaml.safe_load(f)
			except:
				raise IOError("Failed to read profile")
		return profile_dict

	def _save_profile(self, path, profile, allow_overwrite = True):
		print "SAVE PROFILE FUNCTION"
		import yaml
		with octoprint.util.atomic_write(path, "wb") as f:
			yaml.safe_dump(profile, f, default_flow_style = False, indent= "  ", allow_unicode = True)

	def get_slicer_default_profile(self):
		print "GET DEFAULT PROFILE FUNCTION"
		path = self._settings.get(["default_profile"])
		if not path:
			path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "profiles", "default.profile.yaml")
		return self.get_slicer_profile(path)

	def save_slicer_profile(self, path, profile, allow_overwrite = True, overrides = None):
		print "SAVE SLICER PROFILE FUNCTION"
		new_profile = Profile.merge_profile(profile.data, overrides = overrides)
		if profile.display_name is not None:
			new_profile["_display_name"] = profile.display_name
		if profile.description is not None:
			new_profile["_description"] = profile.description
		self._save_profile(path, new_profile, allow_overwrite = allow_overwrite)

	def get_slicer_profile(self, path):
		print "GET SLICER PROFILE FUNCTION"
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
