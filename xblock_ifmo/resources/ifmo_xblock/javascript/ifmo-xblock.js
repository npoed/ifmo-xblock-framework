function IfmoXBlockStudentView(runtime, element)
{
    this.runtime = runtime;
    this.element = element;

    this.helpers = {

        deplainify: function(obj)
        {
            for (var key in obj) {
                try {
                    if (obj.hasOwnProperty(key)) {
                        obj[key] = deplainify(JSON.parse(obj[key]));
                    }
                } catch (e) {
                    console.log('failed to deplainify', obj);
                }
            }
            return obj;
        },

        disable_controllers: function(context)
        {
            $(context).find("input,button").addClass('disabled').attr("disabled", "disabled");
        },

        enable_controllers: function(context)
        {
            $(context).find("input,button").removeClass('disabled').removeAttr("disabled");
        }

    };

    this.hooks = {};

    this.template = {};

}

xblock_mixin(IfmoXBlockStudentView.prototype, {
    init_xblock_ready: function($, _) {
        var self = this;
        if (require === undefined) {
            function loadjs(url) {
                if ((typeof $ifmo_xblock_loaded_js === 'undefined') || ($ifmo_xblock_loaded_js === undefined)) {
                    $ifmo_xblock_loaded_js = {}
                }
                if (!(url in $ifmo_xblock_loaded_js)) {
                    $("<script>").attr("type", "text/javascript").attr("src", url).appendTo(self.element);
                    $ifmo_xblock_loaded_js[url] = 1;
                }
                console.log($ifmo_xblock_loaded_js);
            }
            loadjs("/static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js");
            loadjs("/static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js");
            self.init_xblock($, _);
        } else {
            require(["jquery", "underscore", "jquery.fileupload"], self.init_xblock);
        }
        init_modals(self.runtime, self.element, $, _, self.hooks, self.helpers);
    },
    init_xblock: function($, _) {
        $(this.element).find('.instructor-info-action').leanModal();
    },
    add_hooks: function(self, new_hooks) {
       xblock_mixin(self.hooks, new_hooks); // probably should use _.js?
    },
    add_helpers: function(self, new_helpers) {
       xblock_mixin(self.helpers, new_helpers); // probably should use _.js?
    },
    add_templates: function(self, new_templates) {
       xblock_mixin(self.template, new_templates); // probably should use _.js?
    },
    get_template: function(element, tmpl){
        //console.log($(element).find(tmpl));
        // relies on $ and _ being available
        return _.template($(element).find(tmpl).text());
    }
});
