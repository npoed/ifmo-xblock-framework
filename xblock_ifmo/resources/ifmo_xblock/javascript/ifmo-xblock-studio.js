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
        // Студия в качестве this даёт совсем на эту вьюху и даже не её потомков,
        // а собственный объект, в котором есть разве что name, runtime и element.
        // Поэтому всем потомкам пока что необходимо определять свой собственный save,
        // и передавать через apply нужный this для того, чтобы работал validate() и
        // другие собственные методы.
        //
        // Пример:
        // self.save = function()
        // {
        //     MyXBlockSettingsView.superclass.save.apply(self);
        // };


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
