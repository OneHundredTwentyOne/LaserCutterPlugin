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
import svgConverter


class LaserCutterPlugin(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin,
                        octoprint.plugin.AssetPlugin,
						octoprint.plugin.BlueprintPlugin,
						octoprint.plugin.SlicerPlugin):
	def __init__(self):
		self._logger = logging.getLogger("octoprint.plugins.lasercutter")
		self._lasercutter_logger = logging.getLogger("octoprint.plugins.lasercutter")

		#lets the plugin check jobs across different threads
		import threading
		self._slicing_commands = dict()
		self._cancelled_jobs = []
		self._job_mutex = threading.Lock()

	def get_template_vars(self):
		return dict(
			homepage = __plugin_url__
		)

	def on_startup(self, host, port):
		lasercutter_logging_handler = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="engine"), maxBytes=2*1024*1024)
		lasercutter_logging_handler.setFormatter(logging.Formatter("%(asctime)s %*(message)s"))
		lasercutter_logging_handler.setLevel(logging.DEBUG)

		self._lasercutter_logger.addHandler(lasercutter_logging_handler)
		self._lasercutter_logger.setLevel(logging.DEBUG if self._settings.get_boolean(["debug-logging"]) else logging.CRITICAL)
		self._lasercutter_logger.propagate = False

	@octoprint.plugin.BlueprintPlugin.route("/import", methods=["POST"])
	def import_lasercutter_profile(self):
		import datetime
		import tempfile

		from octoprint.server import slicingManager

		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		if input_upload_name in flask.request.values and input_upload_path in flask.request.values:
			filename = flask.request.values[input_upload_name]
			try:
				profile_dict = Profile.from_lasercutter_ini(flask.request.values[input_upload_path])
			except Exception as e:
				self.logger.exception("Error while attempting to convert the uploaded profile")
				return flask.make_response("Something went wrong while converting imported profile: {message}".format(message=str(e)), 500)

		else:
			self.logger.warn("No profile file included")
			return flask.make_response("No file included", 400)

		if profile_dict is None:
			self._logger.warn("No profile file included, cancelling operation")
			return flask.make_response("Could not convert lasercutter profile", 400)

		name, _ = os.path.splitext(filename)

		profile_name = _sanitize_name(name)
		profile_display_name = name
		profile_description = "Imported from {filename} on {date}".format(filename=filename, date=octoprint.util.get_formatted_datetime(datetime.datetime.now()))
		profile_allow_overwrite = False

		#overrides
		if "name" in flask.request.values:
			profile_name = flask.request.values["name"]
		if "displayName" in flask.request.values:
			profile_display_name = flask.request.values["displayName"]
		if "description" in flask.request.values:
			description = flask.request.values["description"]
		if "allowOverwrite" in flask.request.values:
			from octoprint.server.api import valid_boolean_trues
			profile_allow_overwrite =  flask.request.values["allowOverwrite"] in valid_boolean_trues

		try:
			slicingManager.save_profile("lasercutter",profile_name,profile_dict,
										allow_overwrite = profile_allow_overwrite, display_name = profile_display_name,
										description = profile._description)
		except octoprint.slicing.ProfileAlreadyExists:
			self._logger.warn("Profile {profile_name} already exists, aborting".format(**locals()))
			return flask.make_response("A profile named {profile_name} already exists for slicer cura".format(**locals()), 409)

		result = dict(
			resource = flask.url_for("api.slicingGetSlicerProfile", slicer = "lasercutter", name = profile_name, external = True),
			displayName = profile_display_name,
			description = profile_description
		)
		r = flask.make_response(flask.jsonify(result), 201)
		r.headers["Location"] = result["resource"]
		return r

	def on_settings_save(self, data):
		old_debug_logging = self._settings.get_boolean(["debug_logging"])

		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		new_debug_logging = self._settings.get_boolean(["debug_logging"])
		if old_debug_logging != new_debug_logging:
			if new_debug_logging:
				self._lasercutter_logger.setLevel(logging.DEBUG)
			else:
				self._lasercutter_logger.setLevel(logging.CRITICAL)

	def get_settings_defaults(self):
		return dict(
			lasercutter = None,
			default_profile = None,
			debug_logging = False
		)


	def is_slicer_configured(self):
		return True

	def get_slicer_properties(self):
		return dict(
			type = "lasercutter",
			name = "lasercutter",
			same_device = True,
			progress_report = True,
			source_file_types = ["svg"],
			destination_extensions=["gco", "gcode", "g"]
		)

	def get_slicer_default_profile(self):
		path = self._settings.get([	"default_profile"])
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
			display_name = profile_dict["_description"]
			del profile_dict["_description"]
		properties = self.get_slicer_properties()
		return octoprint.slicing.SlicingProfile(properties["type"], "unknown", profile_dict, display_name=display_name, description=description)

	def save_slicer_profile(self,path,profile,allow_overwrite=True, overrides=None):
		new_profile = Profile.merge_profile(profile.data, overrides = overrides)
		if profile.display_name is not None:
			new_profile["_display_name"] = profile.display_name
		if profile.description is not None:
			new_profile["_description"] = profile.description
		self.save_slicer_profile(path, new_profile,allow_overwrite=allow_overwrite)

	def do_slice(self, model_path, printer_profile, machinecode_path=None, profile_path=None,
				 position=None, on_progress=None, on_progress_args=None, on_progress_kwargs=None):
		#insert Peter's slicer here
		test = svgConverter.test()
		print test

	def cancel_slicing(self, machinecode_path):
		with self_job_mutex:
			if machinecode_path in self._slicing_commands:
				self._cancelled_jobs.append(machinecode_path)
				command = self._slicing_commands[machinecode_path]
				if command is not None:
					command.terminate()
				self._logger.info(u"Cancelled slicing of file")

	def _load_profile(self,path):
		import yaml
		profile_dict = dict()
		with open(path, "r") as f:
			try:
				profile_dict = yaml.safe_load(f)
			except:
				raise IOError("Couldn't read profile from {path}".format(path=path))
		return profile_dict

	def _save_profile(self, path, profile, allow_overwrite=True):
			import yaml
			with octoprint.util.atomic_write(path, "wb") as f:
				yaml.safe_dump(profile, f, default_flow_style=False, indent="  ", allow_unicode=True)

	def _convert_to_engine(self, profile_path, printer_profile, posX, posY):
		profile = Profile(self._load_profile(profile_path), printer_profile, posX, posY)
		return profile.convert_to_engine()

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

def _sanitize_name(name):
	if name is None:
		return None

	if "/" in name or "\\" in name:
		raise ValueError("name must not contain / or \\")

	import string
	valid_chars = "-_.() {ascii}{digits}".format(ascii=string.ascii_letters, digits=string.digits)
	sanitized_name = ''.join(c for c in name if c in valid_chars)
	sanitized_name = sanitized_name.replace(" ", "_")
	return sanitized_name.lower()

__plugin_name__ = "Laser Cutter"
__plugin_implementation__ = LaserCutterPlugin()
__plugin_url__ = "https://github.com/thepangman/OctoPrint-LaserCutter.git"
