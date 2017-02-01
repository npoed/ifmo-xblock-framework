# -*- coding: utf-8 -*-

from ifmo_submissions import api as ifmo_submissions_api
from submissions import api as submissions_api
from xblock.core import XBlock

from .xblock_ajax import AjaxHandlerMixin
from .xblock_ifmo import IfmoXBlock
from ..utils import datetime_mapper, deep_update

from ..fragment import FragmentMakoChain


@IfmoXBlock.register_resource_dir("../resources")
class SubmissionsMixin(AjaxHandlerMixin):

    submission_type = "xblock"

    def student_view(self, context=None):

        fragment = FragmentMakoChain(base=super(SubmissionsMixin, self).student_view(),
                                     lookup_dirs=self.get_template_dirs())
        fragment.add_content(self.load_template('xblock_ifmo/student_views/submissions.mako'))
        fragment.add_javascript(self.load_js('modals/submissions-info-modal.js'))

        context = context or {}
        deep_update(context, {'render_context': self.get_student_context()})
        fragment.add_context(context)

        return fragment

    @XBlock.json_handler
    def get_submissions_data(self, data, suffix=''):

        def result(message, success=True, response_type=None):
            return {
                "success": success,
                "type": response_type,
                "message": message,
            }

        def get_anon_id(username):
            return self.runtime.service(self, 'user').get_anonymous_user_id(username, str(self.course_id))

        def extract_user_and_attempt(user_and_attempt):
            submission_param = user_and_attempt.split('+')
            return (submission_param[0],
                    get_anon_id(submission_param[0]),
                    submission_param[1] if len(submission_param) > 1 else None)

        time_format = '%d.%m.%Y %H:%M:%S UTC'

        (real_username, anon_id, attempt_id) = extract_user_and_attempt(data.get('submission_id'))

        # Ensure user exists
        if anon_id is None:
            return result("User %s not found." % real_username, success=False)

        student_dict = self.student_submission_dict(anon_student_id=anon_id)

        # Get all attempts
        if attempt_id is None:

            submissions = submissions_api.get_submissions(student_dict)

            result_submissions = [datetime_mapper(x, time_format) for x in submissions]

            response = {
                'username': real_username,
                'submissions': result_submissions,
            }

            return result(response, response_type="submissions")

        # Get specific attempt
        else:

            response = ifmo_submissions_api.get_submission_annotation(student_dict, attempt_id)
            response['username'] = real_username

            if not response:
                return result("Решение не найдено")

            return result(datetime_mapper(response, time_format), response_type="annotation", success=True)

    def student_submission_dict(self, anon_student_id=None):
        # pylint: disable=no-member
        """
        Returns dict required by the submissions app for creating and
        retrieving submissions for a particular student.
        """
        if anon_student_id is None:
            anon_student_id = self.xmodule_runtime.anonymous_student_id
            assert anon_student_id != (
                'MOCK', "Forgot to call 'personalize' in test."
            )
        return {
            "student_id": anon_student_id,
            "course_id": str(self.course_id),
            "item_id": str(self.location.block_id),
            "item_type": self.submission_type,  # ???
        }
