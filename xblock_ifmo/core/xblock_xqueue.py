# -*- coding=utf-8 -*-

import json

from courseware.models import StudentModule
from xblock.core import XBlock
from xblock.fields import Scope, String, Dict
from xqueue_api.utils import now, make_hashkey, create_student_info
from xqueue_api.xobject import XObjectResult

from ..fragment import FragmentMakoChain
from ..utils import reify
from .xblock_ajax import AjaxHandlerMixin
from .xblock_ifmo import IfmoXBlock


def xqueue_callback(target_class_or_func):

    def wrapped(func):
        assert hasattr(func, '__call__') and hasattr(func, 'func_name')

        def inner(self, *args, **kwargs):
            self.queue_details = {}
            func(self, *args, **kwargs)

        setattr(inner, '_is_xqueue_callback', True)
        setattr(inner, '_xqueue_result_class', target_class)

        return inner

    if not isinstance(target_class_or_func, type):
        target_class = XObjectResult
        return wrapped(target_class_or_func)
    else:
        target_class = target_class_or_func
        return wrapped


@IfmoXBlock.register_resource_dir("../resources")
class XQueueMixin(AjaxHandlerMixin, XBlock):

    queue_name = String(
        scope=Scope.settings,
        default="",
        help="Queue name."
    )

    queue_details = Dict(
        scope=Scope.user_state,
        default=dict(),
    )

    @reify
    def queue_interface(self):
        return self.xmodule_runtime.xqueue['interface']

    @reify
    def queue_key(self):
        return make_hashkey(str(self.xmodule_runtime.seed) + self.queue_time + self.runtime.anonymous_student_id)

    @reify
    def queue_student_info(self):
        return create_student_info(anonymous_student_id=self.xmodule_runtime.anonymous_student_id,
                                   submission_time=self.queue_time)

    @reify
    def queue_time(self):
        return now()

    def save_settings(self, data):

        parent = super(XQueueMixin, self)
        if hasattr(parent, 'save_settings'):
            parent.save_settings(data)

        self.queue_name = data.get('queue_name')
        return {}

    def get_dispatched_url(self, dispatch='score_update'):
        return self.xmodule_runtime.xqueue['construct_callback'](dispatch)

    def get_submission_header(self, dispatch='score_update', access_key_prefix='', extra=None):
        result = {
            'lms_callback_url': self.get_dispatched_url(dispatch),
            'lms_key': "+".join([access_key_prefix, self.queue_key]),
            'queue_name': self.queue_name,
        }
        if extra is not None:
            assert isinstance(extra, dict)
            result.update(extra)
        return json.dumps(result)

    def send_to_queue(self, header=None, body=None, state='QUEUED'):
        self.queue_details = {
            'state': state,
            'key': self.queue_key,
            'time': self.queue_time
        }
        if hasattr(self, 'xqueue_sender_name'):
            try:
                decoded_body = json.loads(body)
                decoded_body['submission_sender'] = self.xqueue_sender_name
                body = json.dumps(decoded_body)
            except KeyError or ValueError:
                pass
        self.queue_interface.send_to_queue(header=header, body=body)

    @xqueue_callback
    def score_update(self, submission_result):

        parent = super(XQueueMixin, self)
        if hasattr(parent, 'score_update'):
            parent.score_update(submission_result)

    def student_view(self):

        fragment = FragmentMakoChain(base=super(XQueueMixin, self).student_view(),
                                     lookup_dirs=self.get_template_dirs())
        fragment.add_content(self.load_template('xblock_ifmo/student_views/xqueue.mako'))
        fragment.add_javascript(self.load_js('modals/queue-info-modal.js'))
        return fragment

    @XBlock.json_handler
    def get_user_queue_status(self, data, suffix=''):
        """
        Получить состояние пользователя в очереди.

        :param data:
        :param suffix:
        :return:
        """
        username = data.get('username')
        error_msg = "Не удалось определить состояние пользователя в очереди. " \
                    "Возможно, пользователь не работал с компонентом."
        try:
            module = StudentModule.objects.get(student__username=username, module_state_key=self.location)
        except StudentModule.DoesNotExist:
            module = None

        if module is not None:
            try:
                state = json.loads(module.state)
                return {"username": username, "queue_status": state.get('queue_details') or error_msg}
            except ValueError or KeyError:
                return error_msg

        else:
            return "Модуль для указанного пользователя не найден."

    @XBlock.json_handler
    def reset_active_status(self, data, suffix=''):
        """
        Сбросить состояние пользователя в очереди.

        :param data:
        :param suffix:
        :return:
        """
        username = data.get('username')
        error_msg = "Не удалось сбросить состояние пользователя в очереди. "
        try:
            module = StudentModule.objects.get(student__username=username, module_state_key=self.location)
        except StudentModule.DoesNotExist:
            module = None

        if module is not None:
            try:
                state = json.loads(module.state)
                state['queue_details'] = {}
                module.state = json.dumps(state)
                module.save()
                return "Состояние пользователя в очереди было сброшено."
            except ValueError or KeyError:
                return error_msg

        else:
            return "Модуль для указанного пользователя не найден."

    @XBlock.json_handler
    def get_active_status_list(self, data, suffix=''):
        """
        Получить список пользователей с активными состояниями и их статус.

        :param data:
        :param suffix:
        :return:
        """
        result = []
        modules = StudentModule.objects.filter(module_state_key=self.location)
        for m in modules:
            try:
                state = json.loads(m.state)
                queue_state = state.get('queue_details').get('state')
                if queue_state in ['GENERATING', 'QUEUED']:
                    result += [{"username": m.student.username, "queue_status": queue_state}]
            except KeyError or ValueError or AttributeError:
                pass
        return result
