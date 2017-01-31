function xblock_mixin(dst, src)
{
    // tobj - вспомогательный объект для фильтрации свойств,
    // которые есть у объекта Object и его прототипа
    var tobj = {};
    for(var x in src){
        // копируем в dst свойства src, кроме тех, которые унаследованы от Object
        if((typeof tobj[x] == "undefined") || (tobj[x] != src[x])){
            dst[x] = src[x];
        }
    }
    // В IE пользовательский метод toString отсутствует в for..in
    if(document.all && !document.isOpera){
        var p = src.toString;
        if(typeof p == "function" && p != dst.toString && p != tobj.toString &&
         p != "\nfunction toString() {\n    [native code]\n}\n"){
            dst.toString = src.toString;
        }
    }
}

function xblock_extend(Child, Parent)
{
    var F = function() { };
    F.prototype = Parent.prototype;
    Child.prototype = new F();
    Child.prototype.constructor = Child;
    Child.superclass = Parent.prototype;
}

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
    pre_init_xblock: function(self, runtime, element, $, _) {
       if (require === undefined) {
            function loadjs(url) {
                $("<script>").attr("type", "text/javascript").attr("src", url).appendTo(element);
            }
            loadjs("/static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js");
            loadjs("/static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js");
            self.init_xblock($, _);
        } else {
            require(["jquery", "underscore", "jquery.fileupload"], self.init_xblock);
        }
        init_modals(runtime, element, $, _, self.hooks, self.helpers);
    },
    init_xblock: function($, _) {
       // pass
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

function IfmoXBlockSettingsView(runtime, element)
{
    var self = this;

    self.runtime = runtime;
    self.element = element;
    self.save_url = runtime.handlerUrl(element, 'save_settings');

    return {
        save: self.save
    }
}

xblock_mixin(IfmoXBlockSettingsView.prototype, {

    save: function() {

        var self = this;
        self.runtime.notify('save', {state: 'start'});

        var validate_result = self.validate();

        var data = {};
        $(self.element).find(".input").each(function(index, input) {
            data[input.name] = input.value;
        });

        if(validate_result.result) {
            $.ajax({
                type: "POST",
                url: self.save_url,
                data: JSON.stringify(data),
                success: function() {
                    self.runtime.notify('save', {state: 'end'});
                }
            });
        } else {
            self.runtime.notify('error', {msg: validate_result.message, title: validate_result.title});
        }
    },
    validate: function() {
        return {
            result: true,
            message: null,
            title: null
        };
    },
    save_url: null,
    runtime: null,
    element: null,
    init_xblock: function($, _) {
        var xblock = $(this.element).find('.ifmo-xblock-editor');
        var data = xblock.data('metadata');
        var template = _.template(xblock.find('.ifmo-xblock-template-base').text());
        xblock.find('.ifmo-xblock-content').html(template(data));
    },
    init_xblock_ready: function($, _) {
        var self = this;
        $(function(){
            self.init_xblock($, _);
        });
    }
});