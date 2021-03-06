#!/usr/bin/python

import unittest, os
import gzip
import cartesian_config


mydir = os.path.dirname(__file__)
testdatadir = os.path.join(mydir, 'unittest_data')


class CartesianConfigTest(unittest.TestCase):
    def _checkDictionaries(self, parser, reference):
        result = list(parser.get_dicts())
        # as the dictionary list is very large, test each item individually:
        self.assertEquals(len(result), len(reference))
        for resdict, refdict in zip(result, reference):
            # checking the dict name first should make some errors more visible
            self.assertEquals(resdict.get('name'), refdict.get('name'))
            self.assertEquals(resdict, refdict)

    def _checkConfigDump(self, config, dump):
        """Check if the parser output matches a config file dump"""
        configpath = os.path.join(testdatadir, config)
        dumppath = os.path.join(testdatadir, dump)

        if dumppath.endswith('.gz'):
            df = gzip.GzipFile(dumppath, 'r')
        else:
            df = open(dumppath, 'r')
        # we could have used pickle, but repr()-based dumps are easier to
        # enerate, debug, and edit
        dumpdata = eval(df.read())

        p = cartesian_config.Parser(configpath)
        self._checkDictionaries(p, dumpdata)


    def _checkStringConfig(self, string, reference):
        p = cartesian_config.Parser()
        p.parse_string(string)
        self._checkDictionaries(p, reference)


    def _checkStringDump(self, string, dump, defaults=False):
        p = cartesian_config.Parser(defaults=defaults)
        p.parse_string(string)

        self._checkDictionaries(p, dump)


    def testSimpleVariant(self):
        self._checkStringConfig("""
            c = abc
            variants:
                - a:
                    x = va
                - b:
                    x = vb
            """,
            [dict(name='a', shortname='a', dep=[], x='va', c='abc'),
             dict(name='b', shortname='b', dep=[], x='vb', c='abc')])


    def testFilterMixing(self):
        self._checkStringDump("""
            variants:
                - unknown_qemu:
                - rhel64:
            only unknown_qemu
            variants:
                - kvm:
                - nokvm:
            variants:
                - testA:
                    nokvm:
                        no unknown_qemu
                - testB:
            """,
            [
                {'dep': [],
                 'name': 'testA.kvm.unknown_qemu',
                 'shortname': 'testA.kvm.unknown_qemu'},
                {'dep': [],
                 'name': 'testB.kvm.unknown_qemu',
                 'shortname': 'testB.kvm.unknown_qemu'},
                {'dep': [],
                 'name': 'testB.nokvm.unknown_qemu',
                 'shortname': 'testB.nokvm.unknown_qemu'},
            ]
            )


    def testNameVariant(self):
        self._checkStringDump("""
            variants tests: # All tests in configuration
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
              - test2:
                   run = "test1"

            variants virt_system:
              - @linux:
              - windows:

            variants host_os:
              - linux:
                   image = linux
              - windows:
                   image = windows

            only (host_os=linux)
            """,
            [
                {'dep': [],
                 'host_os': 'linux',
                 'image': 'linux',
                 'name': '(host_os=linux).(virt_system=linux).(tests=wait).long',
                 'run': 'wait',
                 'shortname': '(host_os=linux).(tests=wait).long',
                 'tests': 'wait',
                 'time': 'short_time',
                 'virt_system': 'linux'},
                {'dep': ['(host_os=linux).(virt_system=linux).(tests=wait).long'],
                 'host_os': 'linux',
                 'image': 'linux',
                 'name': '(host_os=linux).(virt_system=linux).(tests=wait).short',
                 'run': 'wait',
                 'shortname': '(host_os=linux).(tests=wait).short',
                 'tests': 'wait',
                 'time': 'logn_time',
                 'virt_system': 'linux'},
                {'dep': [],
                 'host_os': 'linux',
                 'image': 'linux',
                 'name': '(host_os=linux).(virt_system=linux).(tests=test2)',
                 'run': 'test1',
                 'shortname': '(host_os=linux).(tests=test2)',
                 'tests': 'test2',
                 'virt_system': 'linux'},
                {'dep': [],
                 'host_os': 'linux',
                 'image': 'linux',
                 'name': '(host_os=linux).(virt_system=windows).(tests=wait).long',
                 'run': 'wait',
                 'shortname': '(host_os=linux).(virt_system=windows).(tests=wait).long',
                 'tests': 'wait',
                 'time': 'short_time',
                 'virt_system': 'windows'},
                {'dep': ['(host_os=linux).(virt_system=windows).(tests=wait).long'],
                 'host_os': 'linux',
                 'image': 'linux',
                 'name': '(host_os=linux).(virt_system=windows).(tests=wait).short',
                 'run': 'wait',
                 'shortname': '(host_os=linux).(virt_system=windows).(tests=wait).short',
                 'tests': 'wait',
                 'time': 'logn_time',
                 'virt_system': 'windows'},
                {'dep': [],
                 'host_os': 'linux',
                 'image': 'linux',
                 'name': '(host_os=linux).(virt_system=windows).(tests=test2)',
                 'run': 'test1',
                 'shortname': '(host_os=linux).(virt_system=windows).(tests=test2)',
                 'tests': 'test2',
                 'virt_system': 'windows'},
            ]
            )


    def testDefaults(self):
        self._checkStringDump("""
            variants tests:
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
              - test2:
                   run = "test1"

            variants virt_system [ default=  linux ]:
              - linux:
              - @windows:

            variants host_os:
              - linux:
                   image = linux
              - @windows:
                   image = windows
            """,
            [
                {'dep': [],
                 'host_os': 'windows',
                 'image': 'windows',
                 'name': '(host_os=windows).(virt_system=linux).(tests=wait).long',
                 'run': 'wait',
                 'shortname': '(tests=wait).long',
                 'tests': 'wait',
                 'time': 'short_time',
                 'virt_system': 'linux'},
                {'dep': ['(host_os=windows).(virt_system=linux).(tests=wait).long'],
                 'host_os': 'windows',
                 'image': 'windows',
                 'name': '(host_os=windows).(virt_system=linux).(tests=wait).short',
                 'run': 'wait',
                 'shortname': '(tests=wait).short',
                 'tests': 'wait',
                 'time': 'logn_time',
                 'virt_system': 'linux'},
                {'dep': [],
                 'host_os': 'windows',
                 'image': 'windows',
                 'name': '(host_os=windows).(virt_system=linux).(tests=test2)',
                 'run': 'test1',
                 'shortname': '(tests=test2)',
                 'tests': 'test2',
                 'virt_system': 'linux'},
            ],
            True)

        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants tests [default=system2]:
                  - system1:
                """,
                [],
                True)


    def testDel(self):
        self._checkStringDump("""
            variants tests:
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
              - test2:
                   run = "test1"
            """,
            [
                {'dep': [],
                 'name': '(tests=wait).long',
                 'run': 'wait',
                 'shortname': '(tests=wait).long',
                 'tests': 'wait',
                 'time': 'short_time'},
                {'dep': ['(tests=wait).long'],
                 'name': '(tests=wait).short',
                 'run': 'wait',
                 'shortname': '(tests=wait).short',
                 'tests': 'wait',
                 'time': 'logn_time'},
                {'dep': [],
                 'name': '(tests=test2)',
                 'run': 'test1',
                 'shortname': '(tests=test2)',
                 'tests': 'test2'},
            ],
            True)

        self._checkStringDump("""
            variants tests:
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
              - test2:
                   run = "test1"

            del time
            """,
            [
                {'dep': [],
                 'name': '(tests=wait).long',
                 'run': 'wait',
                 'shortname': '(tests=wait).long',
                 'tests': 'wait'},
                {'dep': ['(tests=wait).long'],
                 'name': '(tests=wait).short',
                 'run': 'wait',
                 'shortname': '(tests=wait).short',
                 'tests': 'wait'},
                {'dep': [],
                 'name': '(tests=test2)',
                 'run': 'test1',
                 'shortname': '(tests=test2)',
                 'tests': 'test2'},
            ],
            True)


    def testError1(self):
        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants tests:
                  wait:
                       run = "wait"
                       variants:
                         - long:
                            time = short_time
                         - short: long
                            time = logn_time
                  - test2:
                       run = "test1"
                """,
                [],
                True)


    def testMissingInclude(self):
        self.assertRaises(cartesian_config.MissingIncludeError,
            self._checkStringDump, """
                include xxxxxxxxx/xxxxxxxxxxx
                """,
            [],
            True)


    def testVariableAssignment(self):
        self._checkStringDump("""
            variants tests:
              -system1:
                    var = 1
                    var = 2
                    var += a
                    var <= b
                    system = 2
                    ddd = ${tests + str(int(system) + 3)}4
                    error = ${tests + str(system + 3)}4
                    s.* ?= ${tests + "ahoj"}4
                    s.* ?+= c
                    s.* ?<= d
                    system += 4
                    var += "test"
            """,
            [
            {'dep': [],
             'name': '(tests=system1)',
             'shortname': '(tests=system1)',
             'system': 'dsystem1ahoj4c4',
             'ddd': 'system154',
             'error': '${tests + str(system + 3)}4',
             'tests': 'system1',
             'var': 'b2atest'},
            ],
            True)


    def testCondition(self):
        self._checkStringDump("""
            variants tests [meta1]:
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
              - test2:
                   run = "test1"

            test2: bbb = aaaa
               aaa = 1
            """,
            [
            {'dep': [],
             'name': '(tests=wait).long',
             'run': 'wait',
             'shortname': '(tests=wait).long',
             'tests': 'wait',
             'time': 'short_time'},
            {'dep': ['(tests=wait).long'],
             'name': '(tests=wait).short',
             'run': 'wait',
             'shortname': '(tests=wait).short',
             'tests': 'wait',
             'time': 'logn_time'},
            {'aaa': '1',
             'bbb': 'aaaa',
             'dep': [],
             'name': '(tests=test2)',
             'run': 'test1',
             'shortname': '(tests=test2)',
             'tests': 'test2'},
            ],
            True)
        self._checkStringDump("""
            variants:
                - a:
                    foo = foo
                    c:
                        foo = bar
                - b:
                    foo = foob
            variants:
                - c:
                    bala = lalalala
                    a:
                       bala = balabala
                - d:
            """,
            [
                {'bala': 'balabala',
                 'dep': [],
                 'foo': 'bar',
                 'name': 'c.a',
                 'shortname': 'c.a'},
                {'bala': 'lalalala',
                 'dep': [],
                 'foo': 'foob',
                 'name': 'c.b',
                 'shortname': 'c.b'},
                {'dep': [], 'foo': 'foo', 'name': 'd.a', 'shortname': 'd.a'},
                {'dep': [], 'foo': 'foob', 'name': 'd.b', 'shortname': 'd.b'},
            ],
            True)


    def testNegativeCondition(self):
        self._checkStringDump("""
            variants tests [meta1]:
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
              - test2:
                   run = "test1"

            !test2: bbb = aaaa
               aaa = 1
            """,
            [
            {'aaa': '1',
             'bbb': 'aaaa',
             'dep': [],
             'name': '(tests=wait).long',
             'run': 'wait',
             'shortname': '(tests=wait).long',
             'tests': 'wait',
             'time': 'short_time'},
            {'aaa': '1',
             'bbb': 'aaaa',
             'dep': ['(tests=wait).long'],
             'name': '(tests=wait).short',
             'run': 'wait',
             'shortname': '(tests=wait).short',
             'tests': 'wait',
             'time': 'logn_time'},
            {'dep': [],
             'name': '(tests=test2)',
             'run': 'test1',
             'shortname': '(tests=test2)',
             'tests': 'test2'},
            ],
            True)


    def testSyntaxErrors(self):
        self.assertRaises(cartesian_config.LexerError,
            self._checkStringDump, """
                variants tests$:
                  - system1:
                        var = 1
                        var = 2
                        var += a
                        var <= b
                        system = 2
                        s.* ?= ${tests}4
                        s.* ?+= c
                        s.* ?<= d
                        system += 4
                """,
                [],
                True)

        self.assertRaises(cartesian_config.LexerError,
            self._checkStringDump, """
                variants tests [defaul$$$$t=system1]:
                  - system1:
                """,
                [],
                True)

        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants tests [default=system1] wrong:
                  - system1:
                """,
                [],
                True)

        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                only xxx...yyy
                """,
                [],
                True)

        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                only xxx..,yyy
                """,
                [],
                True)

        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                aaabbbb.ddd
                """,
                [],
                True)


        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                aaa.bbb:
                  variants test:
                     -sss:
                """,
                [],
                True)


        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants test [sss = bbb:
                     -sss:
                """,
                [],
                True)


        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants test [default]:
                     -sss:
                """,
                [],
                True)


        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants test [default] ddd:
                     -sss:
                """,
                [],
                True)


        self.assertRaises(cartesian_config.ParserError,
            self._checkStringDump, """
                variants test [default] ddd
                """,
                [],
                True)



    def testComplicatedFilter(self):
        self._checkStringDump("""
            variants tests:
              - wait:
                   run = "wait"
                   variants:
                     - long:
                        time = short_time
                     - short: long
                        time = logn_time
                        only (host_os=linux), ( guest_os =    linux  )
              - test2:
                   run = "test1"

            variants guest_os:
              - linux:
                    install = linux
                    no (tests=wait)..short
              - windows:
                    install = windows
                    only test2

            variants host_os:
              - linux:
                    start = linux
              - windows:
                    start = windows
                    only test2
            """,
            [
             {'dep': [],
             'guest_os': 'linux',
             'host_os': 'linux',
             'install': 'linux',
             'name': '(host_os=linux).(guest_os=linux).(tests=wait).long',
             'run': 'wait',
             'shortname': '(host_os=linux).(guest_os=linux).(tests=wait).long',
             'start': 'linux',
             'tests': 'wait',
             'time': 'short_time'},
            {'dep': [],
             'guest_os': 'linux',
             'host_os': 'linux',
             'install': 'linux',
             'name': '(host_os=linux).(guest_os=linux).(tests=test2)',
             'run': 'test1',
             'shortname': '(host_os=linux).(guest_os=linux).(tests=test2)',
             'start': 'linux',
             'tests': 'test2'},
            {'dep': [],
             'guest_os': 'windows',
             'host_os': 'linux',
             'install': 'windows',
             'name': '(host_os=linux).(guest_os=windows).(tests=test2)',
             'run': 'test1',
             'shortname': '(host_os=linux).(guest_os=windows).(tests=test2)',
             'start': 'linux',
             'tests': 'test2'},
            {'dep': [],
             'guest_os': 'linux',
             'host_os': 'windows',
             'install': 'linux',
             'name': '(host_os=windows).(guest_os=linux).(tests=test2)',
             'run': 'test1',
             'shortname': '(host_os=windows).(guest_os=linux).(tests=test2)',
             'start': 'windows',
             'tests': 'test2'},
            {'dep': [],
             'guest_os': 'windows',
             'host_os': 'windows',
             'install': 'windows',
             'name': '(host_os=windows).(guest_os=windows).(tests=test2)',
             'run': 'test1',
             'shortname': '(host_os=windows).(guest_os=windows).(tests=test2)',
             'start': 'windows',
             'tests': 'test2'},
             ],
             True)

        f = "only xxx.yyy..(xxx=333).aaa, ddd (eeee) rrr.aaa"

        self._checkStringDump(f, [], True)

        lexer = cartesian_config.Lexer(cartesian_config.StrReader(f))
        lexer.set_prev_indent(-1)
        lexer.get_next_check([cartesian_config.LIndent])
        lexer.get_next_check([cartesian_config.LOnly])
        p_filter = cartesian_config.parse_filter(lexer, lexer.rest_line())
        self.assertEquals(p_filter,
                          [[[cartesian_config.Label("xxx"),
                             cartesian_config.Label("yyy")],
                            [cartesian_config.Label("xxx", "333"),
                             cartesian_config.Label("aaa")]],
                           [[cartesian_config.Label("ddd")]],
                           [[cartesian_config.Label("eeee")]],
                           [[cartesian_config.Label("rrr"),
                             cartesian_config.Label("aaa")]]],
                          "Failed to parse filter.")


    def testHugeTest1(self):
        self._checkConfigDump('testcfg.huge/test1.cfg',
                              'testcfg.huge/test1.cfg.repr.gz')

if __name__ == '__main__':
    unittest.main()
