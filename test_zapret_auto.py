# -*- coding: utf-8 -*-
import unittest
from zapret_auto import parse_service_query, STRATEGIES, REQUIRED_BINARIES, ensure_binaries, get_strategy_flags

class TestZapretAuto(unittest.TestCase):
    def test_parse_service_running(self):
        sample = """
SERVICE_NAME: winws
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING
                                (STOPPABLE, NOT_PAUSABLE, ACCEPTS_SHUTDOWN)
"""
        self.assertEqual(parse_service_query(sample), "RUNNING")

    def test_parse_service_stopped(self):
        sample = """
SERVICE_NAME: winws
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 1  STOPPED
"""
        self.assertEqual(parse_service_query(sample), "STOPPED")

    def test_parse_service_not_installed(self):
        sample = "[SC] OpenService FAILED 1060: The specified service does not exist as an installed service."
        self.assertEqual(parse_service_query(sample), "NOT_INSTALLED")

    def test_strategies_count(self):
        self.assertGreaterEqual(len(STRATEGIES), 5)
        for s in STRATEGIES:
            self.assertIn("name", s)
            self.assertIn("name_en", s)
            flags = get_strategy_flags(s["id"])
            self.assertIn("--dpi-desync", flags)

    def test_required_binaries(self):
        self.assertIn("winws.exe", REQUIRED_BINARIES)
        self.assertIn("WinDivert.dll", REQUIRED_BINARIES)
        self.assertIn("WinDivert64.sys", REQUIRED_BINARIES)
        self.assertIn("cygwin1.dll", REQUIRED_BINARIES)
        self.assertIn("ACTIVE_DISCORD_UDP.bin", REQUIRED_BINARIES)
        self.assertIn("tls_clienthello_www_google_com.bin", REQUIRED_BINARIES)
        self.assertIn("quic_initial_www_google_com.bin", REQUIRED_BINARIES)
        self.assertIn("tls_clienthello_4pda_to.bin", REQUIRED_BINARIES)
        self.assertTrue(ensure_binaries())

if __name__ == "__main__":
    unittest.main()
