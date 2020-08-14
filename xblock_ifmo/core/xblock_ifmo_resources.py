import collections
import inspect
import itertools
from path import Path

from django.template import Context, Template

from ..utils import convert_xblock_name, reify_f


class ResourcesMixin(object):

    resource_dirs = collections.defaultdict(set)

    def render_template(self, template_path, context=None):
        """
        Evaluate a template by resource path, applying the provided context
        """
        if context is None:
            context = {}
        template_str = self.load_resource(template_path)
        template = Template(template_str)
        return template.render(Context(context))

    def load_resource(self, resource_path, utf8=True):
        """
        Gets the content of a resource
        """
        resource_content = None
        for d in itertools.chain.from_iterable([self.resource_dirs[x] for x in inspect.getmro(self.__class__)]):
            try:
                with open(d / resource_path) as f:
                    resource_content = f.read()
                    break
            except IOError:
                continue
        if resource_content is None:
            raise IOError("Resource %s not found" % resource_path)
        if utf8:
            resource_content = resource_content.decode('utf-8')
        return resource_content
        # return unicode(resource_content)

    def load_js(self, js_name):
        js_name = 'javascript/%s' % js_name
        return self.load_resource(js_name)

    def load_template(self, template_name, context=None, render=False, utf8=True):
        template_name = 'templates/%s' % template_name
        if render:
            return self.render_template(template_name, context)
        else:
            return self.load_resource(template_name, utf8=utf8)

    @reify_f
    def get_template_dirs(self):
        iter_dirs = itertools.chain.from_iterable([self.resource_dirs[x] for x in inspect.getmro(self.__class__)])
        return [d / "templates" for d in iter_dirs if d.exists()]  # probably should check (d / "templates").exists()?

    def load_css(self, css_name):
        css_name = 'styles/%s' % css_name
        return self.load_resource(css_name)

    @classmethod
    def register_resource_dir(cls, resource_dir=None, capitalize=None):

        def _register_template_path(clz):
            r_dir = resource_dir or ("resources/%s" % convert_xblock_name(clz, capitalize))
            cls.resource_dirs[clz].add(
                (Path(inspect.getfile(clz)).dirname().abspath() / r_dir).normpath()
            )
            return clz
        return _register_template_path
