$(function() {
    function LaserCutterViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];
        self.slicingViewModel = parameters[2];

        self.filename = ko.observable();

        self.placeholderName = ko.observable();
        self.placeholderDisplayName = ko.observable();
        self.placeholderDesciption = ko.observable();

        self.profileName = ko.observable();
        self.profileDisplayName = ko.observable();
        self.profileDescription = ko.observable();
        self.profileAllowOverwrite = ko.observable();

        self.uploadElement = $("settings-lasercutter-import");
        self.uploadButton  = $("settings-lasercutter-import-start");

        self.profiles = new ItemListHelper(
            "plugin_lasercutter_profiles",
            {
                "id": function(a,b){
                    if (a["key"].toLocaleLowerCase() < b["key"].toLocaleLowerCase()){
                        return -1;
                    }
                    if (a["key"].toLocaleLowerCase() > b["key"].toLocaleLowerCase()){
                        return -1;
                    }
                    return 0;
                },
                "name": function(a,b){
                    var name1 = a.name();
                    if(name1 === undefined){
                        name1 = "";
                    }
                    var name2 = b.name();
                    if(name2 === undefined){
                        name2 = "";
                    }
                    if(name1.toLocaleLowerCase() < name2.toLocaleLowerCase()){
                        return -1;
                    }
                    if(name1.toLocaleLowerCase() < name2.toLocaleLowerCase()){
                        return -1;
                    }
                    return 0;
                }
            }, {}, "id", [], [], 5
        );

        self.uploadElement.fileupload({
            dataType: "json",
            maxNumberOfFiles: 1,
            autoUpload: false,
            add: function(e, data) {
                if (data.files.length == 0) {
                    return false;
                }
                self.fileName(data.files[0].name);
                var name = self.fileName().substr(0, self.fileName().lastIndexOf("."));
                self.placeholderName(self._sanitize(name).toLowerCase());
                self.placeholderDisplayName(name);
                self.placeholderDescription("Imported from " + self.fileName() + " on " + formatDate(new Date().getTime() / 1000));
                self.uploadButton.unbind("click");
                self.uploadButton.on("click", function() {
                    var form = {
                        allowOverwrite: self.profileAllowOverwrite()
                    };

                    if (self.profileName() !== undefined) {
                        form["name"] = self.profileName();
                    }
                    if (self.profileDisplayName() !== undefined) {
                        form["displayName"] = self.profileDisplayName();
                    }
                    if (self.profileDescription() !== undefined) {
                        form["description"] = self.profileDescription();
                    }
                    data.formData = form;
                    data.submit();
                });
            },
            done: function(e, data) {
                self.fileName(undefined);
                self.placeholderName(undefined);
                self.placeholderDisplayName(undefined);
                self.placeholderDescription(undefined);
                self.profileName(undefined);
                self.profileDisplayName(undefined);
                self.profileDescription(undefined);
                self.profileAllowOverwrite(true);
                $("#settings_plugin_lasercutter_import").modal("hide");
                self.requestData();
                self.slicingViewModel.requestData();
            }
        });

        self.removeProfile = function(data) {
            if (!data.resource) {
                return;
            }

            self.profiles.removeItem(function(item) {
                return (item.key == data.key);
            });

            $.ajax({
                url: data.resource(),
                type: "DELETE",
                success: function() {
                    self.requestData();
                    self.slicingViewModel.requestData();
                }
            });
        };

        self.makeProfileDefault = function(data){
            if(!data.resources){
                return;
            }

            _.each(self.profiles.items(),function(item){
               item.isdefault(false);
            });

            var item = self.profiles.getItem(function(item){
                return item.key == data.key;
            });
            if(item !== undefined){
                item.isdefault(true);
            }

            $.ajax({
                url: data.resource(),
                type: "PATCH",
                dataType: "json",
                data: JSON.stringify({default: true}),
                contentType: "application/json; charset=UTF-8",
                success: function() {
                    self.requestData();
                }
            });
        };

        self.showImportProfileDialog = function(){
          $("#settings_plugin_lasercutter_import").modal("show");
        };

        self.requestData = function(){
            $.ajax({
                url: API_BASEURL + "slicing/lasercutter/profiles",
                type: "GET",
                dataType: "json",
                success: self.fromResponse
            });
        };

        self.fromResponse = function(data){
            var profiles = [];
            _.each(_.keys(data), function(key){
                profiles.push({
                    key: key,
                    name: ko.observable(data[key].displayName),
                    description: ko.observable(data[key].description),
                    isdefault: ko.observable(data[key].default),
                    resource: ko.observable(data[key].resource)
                })
            });
            self.profile.updateItems(profiles);
        };

        self.onBeforeBinding = function(){
            self.settings = self.settingsViewModel.settings;
            self.requestData();
        };
    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        LaserCutterViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["loginStateViewModel, settingsViewModel, slicingViewModel"],
        "#settings_plugin_lasercutter"
    ]);
});
