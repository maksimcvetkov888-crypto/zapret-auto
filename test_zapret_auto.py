# -*- coding: utf-8 -*-
import unittest
from zapret_auto import (
    parse_service_query,
    STRATEGIES,
    REQUIRED_BINARIES,
    PAYLOAD_FILES,
    LIST_FILES,
    EXTRA_GENERAL_DOMAINS,
    ensure_binaries,
    get_strategy_flags
)

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

    def test_strategies_flowseal(self):
        self.assertEqual(len(STRATEGIES), 5)
        for s in STRATEGIES:
            self.assertIn("name", s)
            self.assertIn("name_en", s)
            flags = get_strategy_flags(s["id"])
            self.assertIn("--dpi-desync", flags)
            self.assertIn("list-general.txt", flags)
            self.assertIn("list-google.txt", flags)
            self.assertIn("ACTIVE_DISCORD_UDP.bin", flags)

    def test_required_binaries_and_payloads(self):
        self.assertIn("winws.exe", REQUIRED_BINARIES)
        self.assertIn("WinDivert.dll", REQUIRED_BINARIES)
        self.assertIn("WinDivert64.sys", REQUIRED_BINARIES)
        self.assertIn("cygwin1.dll", REQUIRED_BINARIES)
        for p in ["ACTIVE_DISCORD_UDP.bin", "ACTIVE_GAME_UDP.bin", "stun.bin", "stun2.bin", "tls_clienthello_max_ru.bin"]:
            self.assertIn(p, PAYLOAD_FILES)
            self.assertIn(p, REQUIRED_BINARIES)

    def test_telegram_and_spotify_domains(self):
        self.assertIn("t.me", EXTRA_GENERAL_DOMAINS)
        self.assertIn("web.telegram.org", EXTRA_GENERAL_DOMAINS)
        self.assertIn("spotify.com", EXTRA_GENERAL_DOMAINS)
        self.assertIn("spclient.wg.spotify.com", EXTRA_GENERAL_DOMAINS)

    def test_ensure_binaries(self):
        self.assertTrue(ensure_binaries())

if __name__ == "__main__":
    unittest.main()
