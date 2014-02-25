import os

import pytest
from flexmock import flexmock

from devassistant.command import Command
from devassistant.command_helpers import DialogHelper
from devassistant.command_runners import AskCommandRunner, CallCommandRunner, ClCommandRunner, \
    Jinja2Runner, LogCommandRunner
from devassistant.exceptions import CommandException, RunException

from test.logger import TestLoggingHandler


class TestAskCommandRunner(object):
    # There is mocking code duplication, because (at least) with flexmock 0.9.6
    # and pytest 2.4.2, the mocking in setup_method isn't applied in test
    # methods.
    def setup_method(self, method):
        self.acr = AskCommandRunner

    def test_matches(self):
        assert self.acr.matches(Command('ask_foo', [], False, []))
        assert not self.acr.matches(Command('foo', [], False, []))

    def test_run_password(self):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_password').and_return('foobar')
        comm = Command('ask_password', {}, False, {})
        res = self.acr.run(comm)

        assert res[0] is True
        assert res[1] == 'foobar'

    @pytest.mark.parametrize('decision', [True, False])
    def test_run_confirm(self, decision):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_confirm_with_message').and_return(decision)
        comm = Command('ask_confirm', {}, True, {})
        res = self.acr.run(comm)

        assert res[0] is decision
        assert res[1] == decision


class TestCallCommandRunner(object):
    def setup_method(self, method):
        self.ccr = CallCommandRunner

    def test_matches(self):
        assert self.ccr.matches(Command('call', None, False, None))
        assert self.ccr.matches(Command('use', None, False, None))
        assert not self.ccr.matches(Command('foo', None, False, None))

    @pytest.mark.parametrize('command', ['self', 'super'])
    def test_is_snippet_call_fails(self, command):
        assert not self.ccr.is_snippet_call(command)
        assert not self.ccr.is_snippet_call('{0}.foo'.format(command))

    def test_is_snippet_call_passes(self):
        assert self.ccr.is_snippet_call('foo')

    # TODO test other methods


class TestClCommandRunner(object):
    def setup_method(self, method):
        self.cl = ClCommandRunner
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_command_passes(self):
        self.cl.run(Command('cl', 'true', True, 'true'))

    def test_command_fails(self):
        with pytest.raises(RunException):
            self.cl.run(Command('cl', 'false', True, 'false'))

    def test_run_logs_command_at_debug(self):
        # previously, this test used 'ls', but that is in different locations on different
        # distributions (due to Fedora's usrmove), so use something that should be common
        self.cl.run(Command('cl', 'id', True, 'id'))
        assert ('DEBUG', 'id') in self.tlh.msgs

    def test_run_logs_command_at_info_if_asked(self):
        self.cl.run(Command('cl_i', 'id', True, 'id'))
        assert ('INFO', 'id') in self.tlh.msgs


class TestDependenciesCommandRunner(object):
    pass


class TestDotDevassistantCommandRunner(object):
    pass


class TestGitHubCommandRunner(object):
    pass


class TestJinja2CommandRunner(object):
    def setup_method(self, method):
        self.jr = Jinja2Runner
        self.filesdir = os.path.join(os.path.dirname(__file__), 'fixtures', 'files')

    def is_file_exists(self, tmpdir, f):
        return os.path.isfile(os.path.join(tmpdir.strpath, f))

    def make_sure_file_does_not_exists(self, tmpdir, f):
        fn = os.path.join(tmpdir.strpath, f)
        if (os.path.exists(fn)):
            os.remove(fn)

    def get_file_contents(self, tmpdir, f):
        return open(os.path.join(tmpdir.strpath, f)).read()

    def test_matches(self):
        assert self.jr.matches(Command('jinja_render', None, False, None))

    def test_render_tpl_file_default_case_1(self, tmpdir):
        fn = 'jinja_template.py'
        # Case 1: template name ends w/ '.tpl'
        fntpl = fn + '.tpl'
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'what': 'foo'},
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    True,
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'print("foo")'

    def test_render_tpl_file_default_case_2(self, tmpdir):
        fn = 'jinja_template.py'
        # Case 2: output filename will be the same!
        fntpl = fn
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'what': 'foo'},
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    True,
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'print("foo")'

    def test_render_tpl_file_set_output_case(self, tmpdir):
        # Case 3: set desired output name explicitly
        fn ='rendered_jinja_template.py'
        fntpl = 'jinja_template.py.tpl'
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'what': 'foo'},
               'output': fn,
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    True,
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'print("foo")'


class TestLogCommandRunner(object):
    def setup_method(self, method):
        self.l = LogCommandRunner
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_log(self):
        self.l.run(Command('log_w', 'foo!', True, 'foo!'))
        assert self.tlh.msgs == [('WARNING', 'foo!')]

    def test_log_wrong_level(self):
        with pytest.raises(CommandException):
            self.l.run(Command('log_b', 'bar', True, 'bar'))


class TestSaveProjectCommandRunner(object):
    pass


class TestSCLCommandRunner(object):
    def setup_method(self, method):
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_scl_passes_scls_list_to_command_invocation(self):
        # please don't use $__scls__ in actual assistants :)
        # scl runner has to use the unformatted input
        inp = [{'log_i': '$__scls__'}]
        fmtd_inp = [{'log_i': 'this should not be used'}]
        c = Command('scl enable foo bar', inp, True, fmtd_inp, {})
        c.run()
        assert ('INFO', "[['enable', 'foo', 'bar']]") in self.tlh.msgs
