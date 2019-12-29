from __future__ import absolute_import, print_function, unicode_literals
import unittest
import subprocess
from functional_tests import constants


class FindBugsTestCase(unittest.TestCase):
    def test_sweep_bugs(self):
        out = subprocess.check_output(
            constants.ELLIOTT_CMD
            + [
                "--group=openshift-4.3", "find-bugs", "--mode=sweep",
            ]
        )
        self.assertRegexpMatches(out.decode("utf-8"), "Found \\d+ bugs")
