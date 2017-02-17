#!/usr/bin/python
# pylint: disable=invalid-name
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Driver script to call test cases from source files.
First argument is a parameter file, containing a Python dictionary.
Values in the parameters are:
    modules - tuple of possible modules
    path - string of path or None,
    verbose - boolean to display unittests
"""

import fnmatch
import imp
import logging
import os
import sys
import traceback
import unittest
try:
    import coverage
except ImportError:
    pass
else:
    coverage.process_startup()

try:
    loader = unittest.loader.TestLoader()
except AttributeError:
    loader = unittest.TestLoader()

if not hasattr(loader, 'discover'):
    # for before Py2.7
    class TestLoaderNoDiscover(loader.__class__):
        """Load test cases without using unittest.discover."""
        # ported almost directly from Py2.7 unittest.loader module
        _top_level_dir = None
        def discover(self, start_dir, pattern='test*.py', top_level_dir=None):
            set_implicit_top = False
            if top_level_dir is None and self._top_level_dir is not None:
                top_level_dir = self._top_level_dir
            elif top_level_dir is None:
                set_implicit_top = True
                top_level_dir = start_dir
            self._top_level_dir = top_level_dir = os.path.abspath(top_level_dir)
            if top_level_dir not in sys.path:
                sys.path.insert(0, top_level_dir)
            is_not_importable = False
            if os.path.isdir(os.path.abspath(start_dir)):
                start_dir = os.path.abspath(start_dir)
                if start_dir != top_level_dir:
                    is_not_importable = not \
                        os.path.isfile(os.path.join(start_dir, '__init__.py'))
            else:  # a module/package name
                try:
                    __import__(start_dir)
                except ImportError:
                    is_not_importable = True
                else:
                    the_module = sys.modules[start_dir]
                    top_part = start_dir.split('.')[0]
                    start_dir = os.path.abspath(
                        os.path.dirname(the_module.__file__)
                    )
                    if set_implicit_top:
                        module = sys.modules[top_part]
                        full_path = os.path.abspath(module.__file__)
                        # pylint: disable=protected-access
                        if os.path.basename(full_path).lower(). \
                                __startswith('__init__.py'):
                            self._top_level_dir = os.path.dirname(
                                os.path.dirname(full_path)
                            )
                        else:
                            self._top_level_dir = os.path.dirname(full_path)
                        sys.path.remove(top_level_dir)
            if is_not_importable:
                raise ImportError(
                    'Start directory is not importable: %s' % start_dir
                )
            tests = list(self._find_tests(start_dir, pattern))
            return self.suiteClass(tests)

        def _find_tests_file(self, path, full_path, pattern):
            """Handle test cases found in a file."""
            if not fnmatch.fnmatch(path, '[_a-z]*.py'):
                # value Python identifiers only
                return
            if not fnmatch.fnmatch(path, pattern):
                return
            try:
                name = self._get_name_from_path(full_path)
                module = self._get_module_from_name(name)
            # pylint: disable=broad-except
            except Exception:
                yield self._make_failed_import_test(
                    name, self.suiteClass
                )
            else:
                mod_file = os.path.abspath(
                    getattr(module, '__file__', full_path)
                )
                realpath = os.path.splitext(mod_file)[0]
                fullpath_noext = os.path.splitext(full_path)[0]
                if realpath.lower() != fullpath_noext.lower():
                    module_dir = os.path.dirname(realpath)
                    mod_name = os.path.splitext(
                        os.path.basename(full_path)
                    )[0]
                    expected_dir = os.path.dirname(full_path)
                    msg = ('%r module incorrectly imported from %r. '
                           'Expected %r. Is this moduled globally '
                           'installed?')
                    raise ImportError(
                        msg % (mod_name, module_dir, expected_dir)
                    )
                yield self.loadTestsFromModule(module)

        def _find_tests_dir(self, path, full_path, pattern):
            """Handle test cases found in a directory."""
            if not os.path.isfile(os.path.join(full_path, '__init__.py')):
                return
            load_tests = None
            tests = None
            if fnmatch.fnmatch(path, pattern):
                name = self._get_name_from_path(full_path)
                package = self._get_module_from_name(name)
                if package is not None:
                    load_tests = getattr(package, 'load_tests', None)
                    tests = self.loadTestsFromModule(
                        package, use_load_tests=False
                    )
            if load_tests is None:
                if tests is not None:
                    yield tests
                for test in self._find_tests(full_path, pattern):
                    yield test
            else:
                try:
                    yield load_tests(self, tests, pattern)
                #pylint: disable=broad-except
                except Exception:
                    yield self._make_failed_load_tests(
                        package.__name__,
                        sys.exc_info()[1], self.suiteClass
                    )

        def _find_tests(self, start_dir, pattern):
            for path in os.listdir(start_dir):
                full_path = os.path.join(start_dir, path)
                if os.path.isfile(full_path):
                    self._find_tests_file(path, full_path, pattern)

                elif os.path.isdir(full_path):
                    self._find_tests_dir(path, full_path, pattern)

        def _get_name_from_path(self, path):
            path = os.path.splitext(os.path.normpath(path))[0]
            _relpath = os.path.relpath(path, self._top_level_dir)
            assert not os.path.isabs(_relpath), \
                'Path must be within the project'
            assert not _relpath.startswith('..'), \
                'Path must be within the project'
            name = _relpath.replace(os.path.sep, '.')
            return name

        def _get_module_from_name(self, name):
            try:
                __import__(name)
            except ImportError:
                return None
            else:
                return sys.modules[name]

        @classmethod
        def _make_failed_import_test(cls, name, suiteClass):
            """Return a TestClass subclass wrapped in a suite on error."""
            message = r'Failed to import test module: %s\\n%s' % (
                name, traceback.format_exc()
            )
            return cls._make_failed_test('ModuleImportFailure', name,
                                         ImportError(message), suiteClass)

        @classmethod
        def _make_failed_load_tests(cls, name, exception, suiteClass):
            """Return a TestClass subclass wrapped in a suite on error."""
            return cls._make_failed_test('LoadTestsFailure', name, exception,
                                         suiteClass)

        @staticmethod
        def _make_failed_test(classname, methodname, exception,
                              suiteClass):
            """Generate a failed test case."""
            # pylint: disable=unused-argument
            def testFailure(self):
                """Force an exception captured in closure."""
                raise exception
            attrs = {methodname: testFailure}
            TestClass = type(classname, (unittest.TestCase,), attrs)
            return suiteClass((TestClass(methodname),))

    # pylint: disable=redefined-variable-type
    loader = TestLoaderNoDiscover()


if __name__ == '__main__':
    # pylint: disable=eval-used
    params = eval(sys.argv[1])

    verbose = ('verbose' in params and params['verbose']) and 1 or 0

    try:
        runner = unittest.runner.TextTestRunner(verbosity=verbose)
    except AttributeError:
        runner = unittest.TextTestRunner(verbosity=verbose)
    try:
        suite = unittest.suite.TestSuite()
    #pylint: disable=broad-except
    except Exception:
        suite = unittest.TestSuite()

    real_args = sys.argv[:]
    logging.getLogger('pyerector').setLevel(logging.ERROR)
    try:
        if params['modules']:
            modpath = [os.path.realpath(p) for p in params['path']]
            if not modpath:
                modpath = [os.curdir]
            for modname in params['modules']:
                sys.argv[:] = [modname]
                packet = imp.find_module(modname, modpath)
                mod = imp.load_module(modname, *packet)
                suite.addTests(loader.loadTestsFromModule(mod))
        elif params['path']:
            for modpath in [os.path.realpath(p) for p in params['path']]:
                suite.addTests(loader.discover(modpath))
        else:
            suite.addTests(loader.discover(os.curdir))
        try:
            runner.run(suite)
        except KeyboardInterrupt:
            print
            raise SystemExit(5)
    finally:
        sys.argv[:] = real_args

