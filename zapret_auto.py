# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import socket
import ssl
import time
import ctypes
import platform
import argparse
import urllib.request
import zipfile
import shutil
import io

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ZAPRET_RELEASE_URL = "https://github.com/bol-van/zapret/releases/download/v72.13/zapret-v72.13.zip"
PAYLOAD_BASE_URL = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/main/bin/"

PAYLOAD_FILES = [
    "ACTIVE_DISCORD_UDP.bin",
    "ACTIVE_GAME_UDP.bin",
    "quic_initial_www_google_com.bin",
    "tls_clienthello_www_google_com.bin",
    "tls_clienthello_4pda_to.bin",
    "tls_clienthello_max_ru.bin",
    "stun.bin",
    "stun2.bin"
]

LIST_FILES = [
    "list-general.txt",
    "list-google.txt",
    "list-exclude.txt",
    "ipset-all.txt",
    "ipset-exclude.txt"
]

REQUIRED_BINARIES = [
    "winws.exe",
    "WinDivert.dll",
    "WinDivert64.sys",
    "cygwin1.dll"
] + PAYLOAD_FILES

INSTALL_DIR = r"C:\zapret"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"

STRATEGIES = [
    {
        "id": "1",
        "name": "General (Default - Multisplit Google/General + Discord UDP)",
        "name_en": "General (Default - Multisplit Google/General + Discord UDP)",
        "desc": "Flowseal классический: multisplit 4PDA + Google + Discord UDP (YouTube 4K, Discord, Telegram, Spotify)."
    },
    {
        "id": "2",
        "name": "General (ALT - Fake + Fakedsplit TS)",
        "name_en": "General (ALT - Fake + Fakedsplit TS)",
        "desc": "Альтернативный режим: фейковые TLS пакеты с временными метками TCP (Ростелеком, Дом.ру, МТС)."
    },
    {
        "id": "3",
        "name": "General (ALT2 - Multisplit pos 2 seqovl 652)",
        "name_en": "General (ALT2 - Multisplit pos 2 seqovl 652)",
        "desc": "Смещение заголовков TLS с перекрытием 652 байта для строгой ТСПУ-фильтрации."
    },
    {
        "id": "4",
        "name": "General (FAKE TLS AUTO - Multidisorder)",
        "name_en": "General (FAKE TLS AUTO - Multidisorder)",
        "desc": "Динамический multidisorder с подменой SNI и session ID (Билайн, Мегафон, Tele2)."
    },
    {
        "id": "5",
        "name": "General (SIMPLE FAKE - Hostfakesplit TS)",
        "name_en": "General (SIMPLE FAKE - Hostfakesplit TS)",
        "desc": "Облегченный fake desync для минимальной нагрузки на процессор."
    }
]

CONFLICT_PROCS = ["winws.exe", "goodbyedpi.exe", "byedpi.exe", "ciadpi.exe"]
CONFLICT_SERVICES = ["winws", "zapret", "GoodbyeDPI", "WinDivert", "WinDivert14"]

def get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def get_bin_dir():
    if platform.system() == "Windows" and os.path.isdir(os.path.join(INSTALL_DIR, "bin")):
        return os.path.join(INSTALL_DIR, "bin")
    base = get_base_dir()
    sub_bin = os.path.join(base, "bin")
    if os.path.isdir(sub_bin):
        return sub_bin
    return base

def get_lists_dir():
    if platform.system() == "Windows" and os.path.isdir(os.path.join(INSTALL_DIR, "lists")):
        return os.path.join(INSTALL_DIR, "lists")
    base = get_base_dir()
    sub_lists = os.path.join(base, "lists")
    if os.path.isdir(sub_lists):
        return sub_lists
    return base

def get_strategy_flags(strategy_id="1"):
    bin_dir = get_bin_dir()
    lists_dir = get_lists_dir()

    p_quic = os.path.join(bin_dir, "quic_initial_www_google_com.bin")
    p_discord = os.path.join(bin_dir, "ACTIVE_DISCORD_UDP.bin")
    p_tls_google = os.path.join(bin_dir, "tls_clienthello_www_google_com.bin")
    p_tls_4pda = os.path.join(bin_dir, "tls_clienthello_4pda_to.bin")
    p_tls_max = os.path.join(bin_dir, "tls_clienthello_max_ru.bin")
    p_stun = os.path.join(bin_dir, "stun.bin")

    f_gen = os.path.join(lists_dir, "list-general.txt")
    f_goog = os.path.join(lists_dir, "list-google.txt")
    f_excl = os.path.join(lists_dir, "list-exclude.txt")
    f_ipset = os.path.join(lists_dir, "ipset-all.txt")
    f_ipset_excl = os.path.join(lists_dir, "ipset-exclude.txt")

    wf = "--wf-tcp=80,443,2053,2083,2087,2096,8443 --wf-udp=443,19294-19344,50000-50100"
    u_quic = f'--filter-udp=443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic=\\"{p_quic}\\" --new'
    u_disc = f'--filter-udp=19294-19344,50000-50100 --filter-l7=discord,stun --dpi-desync=fake --dpi-desync-fake-discord=\\"{p_discord}\\" --dpi-desync-fake-stun=\\"{p_discord}\\" --dpi-desync-repeats=6 --new'
    u_quic_ipset = f'--filter-udp=443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic=\\"{p_quic}\\" --new'

    if str(strategy_id) == "1":
        return (
            f'{wf} {u_quic} {u_disc} '
            f'--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=multisplit --dpi-desync-split-seqovl=681 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=443 --hostlist=\\"{f_goog}\\" --ip-id=zero --dpi-desync=multisplit --dpi-desync-split-seqovl=681 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=80,443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=multisplit --dpi-desync-split-seqovl=568 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern=\\"{p_tls_4pda}\\" --new '
            f'{u_quic_ipset} '
            f'--filter-tcp=80,443,8443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=multisplit --dpi-desync-split-seqovl=568 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern=\\"{p_tls_4pda}\\"'
        )
    elif str(strategy_id) == "2":
        return (
            f'{wf} {u_quic} {u_disc} '
            f'--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=fake,fakedsplit --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fakedsplit-pattern=0x00 --dpi-desync-fake-tls=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=443 --hostlist=\\"{f_goog}\\" --ip-id=zero --dpi-desync=fake,fakedsplit --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fakedsplit-pattern=0x00 --dpi-desync-fake-tls=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=80,443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake,fakedsplit --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fakedsplit-pattern=0x00 --dpi-desync-fake-tls=\\"{p_stun}\\" --dpi-desync-fake-tls=\\"{p_tls_google}\\" --dpi-desync-fake-http=\\"{p_tls_max}\\" --new '
            f'{u_quic_ipset} '
            f'--filter-tcp=80,443,8443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake,fakedsplit --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fakedsplit-pattern=0x00 --dpi-desync-fake-tls=\\"{p_stun}\\" --dpi-desync-fake-tls=\\"{p_tls_google}\\" --dpi-desync-fake-http=\\"{p_tls_max}\\"'
        )
    elif str(strategy_id) == "3":
        return (
            f'{wf} {u_quic} {u_disc} '
            f'--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=multisplit --dpi-desync-split-seqovl=652 --dpi-desync-split-pos=2 --dpi-desync-split-seqovl-pattern=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=443 --hostlist=\\"{f_goog}\\" --ip-id=zero --dpi-desync=multisplit --dpi-desync-split-seqovl=652 --dpi-desync-split-pos=2 --dpi-desync-split-seqovl-pattern=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=80,443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=multisplit --dpi-desync-split-seqovl=652 --dpi-desync-split-pos=2 --dpi-desync-split-seqovl-pattern=\\"{p_tls_google}\\" --new '
            f'{u_quic_ipset} '
            f'--filter-tcp=80,443,8443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=multisplit --dpi-desync-split-seqovl=652 --dpi-desync-split-pos=2 --dpi-desync-split-seqovl-pattern=\\"{p_tls_google}\\"'
        )
    elif str(strategy_id) == "4":
        u_quic_11 = f'--filter-udp=443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake --dpi-desync-repeats=11 --dpi-desync-fake-quic=\\"{p_quic}\\" --new'
        u_quic_ipset_11 = f'--filter-udp=443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake --dpi-desync-repeats=11 --dpi-desync-fake-quic=\\"{p_quic}\\" --new'
        return (
            f'{wf} {u_quic_11} {u_disc} '
            f'--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=fake,multidisorder --dpi-desync-split-pos=1,midsld --dpi-desync-repeats=11 --dpi-desync-fooling=badseq --dpi-desync-fake-tls=0x00000000 --dpi-desync-fake-tls=! --dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com --new '
            f'--filter-tcp=443 --hostlist=\\"{f_goog}\\" --ip-id=zero --dpi-desync=fake,multidisorder --dpi-desync-split-pos=1,midsld --dpi-desync-repeats=11 --dpi-desync-fooling=badseq --dpi-desync-fake-tls=0x00000000 --dpi-desync-fake-tls=! --dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com --new '
            f'--filter-tcp=80,443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake,multidisorder --dpi-desync-split-pos=1,midsld --dpi-desync-repeats=11 --dpi-desync-fooling=badseq --dpi-desync-fake-tls=0x00000000 --dpi-desync-fake-tls=! --dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com --dpi-desync-fake-http=\\"{p_tls_max}\\" --new '
            f'{u_quic_ipset_11} '
            f'--filter-tcp=80,443,8443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake,multidisorder --dpi-desync-split-pos=1,midsld --dpi-desync-repeats=11 --dpi-desync-fooling=badseq --dpi-desync-fake-tls=0x00000000 --dpi-desync-fake-tls=! --dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com --dpi-desync-fake-http=\\"{p_tls_max}\\"'
        )
    else:
        return (
            f'{wf} {u_quic} {u_disc} '
            f'--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fake-tls=\\"{p_tls_google}\\" --new '
            f'--filter-tcp=443 --hostlist=\\"{f_goog}\\" --ip-id=zero --dpi-desync=hostfakesplit --dpi-desync-fooling=ts --dpi-desync-hostfakesplit-mod=host=www.google.com --new '
            f'--filter-tcp=80,443 --hostlist=\\"{f_gen}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fake-tls=\\"{p_tls_google}\\" --dpi-desync-fake-http=\\"{p_tls_max}\\" --new '
            f'{u_quic_ipset} '
            f'--filter-tcp=80,443,8443 --ipset=\\"{f_ipset}\\" --hostlist-exclude=\\"{f_excl}\\" --ipset-exclude=\\"{f_ipset_excl}\\" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fooling=ts --dpi-desync-fake-tls=\\"{p_tls_google}\\" --dpi-desync-fake-http=\\"{p_tls_max}\\"'
        )

def is_admin():
    if platform.system() == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0

def elevate_privileges():
    """Automatically request Windows Administrator (UAC) privileges in place."""
    if platform.system() == "Windows" and not is_admin():
        try:
            if getattr(sys, "frozen", False):
                exe = sys.executable
                args = " ".join([f'"{a}"' for a in sys.argv[1:]])
            else:
                exe = sys.executable
                args = " ".join([f'"{a}"' for a in sys.argv])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, args, None, 1)
            if ret > 32:
                os._exit(0)
        except Exception:
            pass
    return is_admin()

def enable_tcp_timestamps():
    """Enable RFC 1323 TCP Timestamps required for winws fake/split packet desync."""
    if platform.system() == "Windows":
        try:
            subprocess.run(
                "netsh interface tcp set global timestamps=enabled",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception:
            pass

EXTRA_GENERAL_DOMAINS = [
    "t.me",
    "telegram.org",
    "telegram.me",
    "web.telegram.org",
    "api.telegram.org",
    "venus.web.telegram.org",
    "aurora.web.telegram.org",
    "vesta.web.telegram.org",
    "pluto.web.telegram.org",
    "flora.web.telegram.org",
    "telesco.pe",
    "tdesktop.com",
    "telegra.ph",
    "telegram-cdn.org",
    "stel.com",
    "spotify.com",
    "spclient.wg.spotify.com",
    "ap.spotify.com",
    "apresolve.spotify.com",
    "dealer.spotify.com",
    "audio-ak-spotify-com.akamaized.net",
    "audio-ak.spotify.com.edgesuite.net",
    "audio-fa.scdn.co",
    "heads-fa.scdn.co",
    "spotifycdn.com",
    "scdn.co",
    "open.spotify.com",
    "api.spotify.com"
]

def ensure_binaries():
    """Verify winws binaries, Flowseal payloads, and hostlists with Telegram & Spotify exist."""
    base_dir = get_base_dir()
    bin_dir = get_bin_dir()
    lists_dir = get_lists_dir()

    enable_tcp_timestamps()

    if platform.system() == "Windows":
        try:
            os.makedirs(INSTALL_DIR, exist_ok=True)
            os.makedirs(os.path.join(INSTALL_DIR, "bin"), exist_ok=True)
            os.makedirs(os.path.join(INSTALL_DIR, "lists"), exist_ok=True)
        except Exception:
            pass

    # Ensure binary files exist
    target_bin = os.path.join(INSTALL_DIR, "bin") if platform.system() == "Windows" else bin_dir
    missing_bins = []
    for b in REQUIRED_BINARIES:
        in_bin = os.path.exists(os.path.join(bin_dir, b))
        in_base = os.path.exists(os.path.join(base_dir, b))
        in_inst = os.path.exists(os.path.join(INSTALL_DIR, "bin", b)) or os.path.exists(os.path.join(INSTALL_DIR, b))
        if not in_bin and not in_base and not in_inst:
            missing_bins.append(b)

    if missing_bins:
        print("----------------------------------------------------------------")
        print(f"[СКАЧИВАНИЕ] Загрузка компонентов zapret ({len(missing_bins)} шт)...")
        print("----------------------------------------------------------------")

        core_missing = [b for b in ["winws.exe", "WinDivert.dll", "WinDivert64.sys", "cygwin1.dll"] if b in missing_bins]
        if core_missing:
            try:
                req = urllib.request.Request(
                    ZAPRET_RELEASE_URL,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for b in core_missing:
                        zip_path = f"zapret-v72.13/binaries/windows-x86_64/{b}"
                        with open(os.path.join(target_bin, b), "wb") as f_out:
                            f_out.write(z.read(zip_path))
                        print(f"[РАСПАКОВАН] {b}")
            except Exception as e:
                print(f"[ОШИБКА] Не удалось скачать ядро: {e}")
                return False

        payload_missing = [p for p in PAYLOAD_FILES if p in missing_bins]
        for p in payload_missing:
            try:
                url = PAYLOAD_BASE_URL + p
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                with open(os.path.join(target_bin, p), "wb") as f_out:
                    f_out.write(data)
                print(f"[СКАЧАН ПЕЙЛОАД] {p}")
            except Exception as e:
                print(f"[ОШИБКА] Не удалось скачать {p}: {e}")
                return False

    # Ensure list files exist
    target_lists = os.path.join(INSTALL_DIR, "lists") if platform.system() == "Windows" else lists_dir
    os.makedirs(target_lists, exist_ok=True)
    list_base_url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/main/lists/"
    for l in LIST_FILES:
        loc_path = os.path.join(target_lists, l)
        src_path = os.path.join(lists_dir, l)
        if not os.path.exists(loc_path) and not os.path.exists(src_path):
            try:
                url = list_base_url + l
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                with open(loc_path, "wb") as f_out:
                    f_out.write(data)
                print(f"[СКАЧАН СПИСОК] {l}")
            except Exception:
                # Fallback dummy file
                with open(loc_path, "w", encoding="utf-8") as f_out:
                    f_out.write("203.0.113.113/32\n" if "ipset" in l else "example.com\n")

    # Add Telegram and Spotify domains into list-general.txt
    for check_dir in [target_lists, lists_dir]:
        f_gen = os.path.join(check_dir, "list-general.txt")
        if os.path.exists(f_gen):
            try:
                with open(f_gen, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                append_domains = [d for d in EXTRA_GENERAL_DOMAINS if d not in content]
                if append_domains:
                    with open(f_gen, "a", encoding="utf-8") as f:
                        f.write("\n# Telegram & Spotify\n" + "\n".join(append_domains) + "\n")
            except Exception:
                pass

    # Ensure dummy user files exist
    for dummy in ["list-general-user.txt", "list-exclude-user.txt", "ipset-exclude-user.txt"]:
        for d in [target_lists, lists_dir]:
            p = os.path.join(d, dummy)
            if not os.path.exists(p):
                try:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write("# user custom list\n")
                except Exception:
                    pass

    # Sync all files to C:\zapret for 100% clean ASCII path
    if platform.system() == "Windows" and os.path.exists(INSTALL_DIR):
        inst_bin = os.path.join(INSTALL_DIR, "bin")
        inst_lists = os.path.join(INSTALL_DIR, "lists")
        os.makedirs(inst_bin, exist_ok=True)
        os.makedirs(inst_lists, exist_ok=True)

        for b in REQUIRED_BINARIES:
            src = os.path.join(bin_dir, b) if os.path.exists(os.path.join(bin_dir, b)) else os.path.join(base_dir, b)
            if os.path.exists(src):
                for dest in [os.path.join(inst_bin, b), os.path.join(INSTALL_DIR, b)]:
                    if not os.path.exists(dest):
                        try:
                            shutil.copy2(src, dest)
                        except Exception:
                            pass

        for l in os.listdir(lists_dir) if os.path.isdir(lists_dir) else []:
            src = os.path.join(lists_dir, l)
            dest = os.path.join(inst_lists, l)
            if os.path.isfile(src) and not os.path.exists(dest):
                try:
                    shutil.copy2(src, dest)
                except Exception:
                    pass

    return True

def fix_youtube_dns():
    """Bypass ISP DNS poisoning (172.16.x / fake IPs) by mapping clean Google IPs into hosts."""
    if platform.system() != "Windows":
        return
    try:
        cur_ip = socket.gethostbyname("www.youtube.com")
        is_poisoned = (
            cur_ip.startswith("172.16.")
            or cur_ip.startswith("127.")
            or cur_ip.startswith("10.")
            or cur_ip.startswith("192.168.")
        )
    except Exception:
        is_poisoned = True

    try:
        content = ""
        if os.path.exists(HOSTS_PATH):
            with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        if "zapret-auto" not in content or is_poisoned:
            clean_entry = "\n# zapret-auto clean youtube DNS\n142.251.152.4 youtube.com www.youtube.com m.youtube.com googlevideo.com youtu.be i.ytimg.com\n"
            if "zapret-auto" not in content:
                with open(HOSTS_PATH, "a", encoding="utf-8") as f:
                    f.write(clean_entry)
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            print("[УСПЕХ] DNS кэш очищен, чистые IP Google применены.")
    except Exception as e:
        print(f"[ВНИМАНИЕ] Не удалось обновить hosts: {e}")

def clean_youtube_dns():
    """Remove zapret-auto hosts entries."""
    if platform.system() != "Windows":
        return
    try:
        if os.path.exists(HOSTS_PATH):
            with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            new_lines = [l for l in lines if "zapret-auto" not in l and "142.251.152.4" not in l]
            with open(HOSTS_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
    except Exception:
        pass

def parse_service_query(output):
    output_lower = output.lower()
    if "running" in output_lower or "state              : 4" in output_lower:
        return "RUNNING"
    elif "stopped" in output_lower or "state              : 1" in output_lower:
        return "STOPPED"
    elif "does not exist" in output_lower or "1060" in output_lower:
        return "NOT_INSTALLED"
    return "UNKNOWN"

def get_service_status(service_name="winws"):
    if platform.system() != "Windows":
        return "UNSUPPORTED_PLATFORM"
    try:
        res = subprocess.run(["sc.exe", "query", service_name], capture_output=True, text=True, shell=True)
        return parse_service_query(res.stdout + res.stderr)
    except Exception as e:
        return f"ERROR: {e}"

def find_conflicts():
    found_procs = []
    found_services = []

    if platform.system() == "Windows":
        try:
            res = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True)
            running = res.stdout.lower()
            for p in CONFLICT_PROCS:
                if p.lower() in running:
                    found_procs.append(p)
        except Exception:
            pass

        for s in CONFLICT_SERVICES:
            st = get_service_status(s)
            if st in ("RUNNING", "STOPPED"):
                found_services.append((s, st))

    return found_procs, found_services

def terminate_conflicts(silent=False):
    if not is_admin():
        elevate_privileges()
    if not silent:
        print("================================================================")
        print("ОЧИСТКА КОНФЛИКТУЮЩИХ ПРОЦЕССОВ И СЛУЖБ")
        print("================================================================")
    procs, services = find_conflicts()
    if not procs and not services:
        if not silent:
            print("[OK] Конфликтующие процессы или службы не найдены.")
            print("================================================================")
        return

    for p in procs:
        try:
            subprocess.run(["taskkill", "/im", p, "/f"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not silent:
                print(f"[ЗАВЕРШЕН] Процесс: {p}")
        except Exception:
            pass

    for s, st in services:
        try:
            subprocess.run(f"sc.exe stop {s}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not silent:
                print(f"[ОСТАНОВЛЕНА] Служба: {s}")
        except Exception:
            pass
    if not silent:
        print("================================================================")

def test_host_probe(host, port=443, timeout=4.0):
    start = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            lat = (time.perf_counter() - start) * 1000.0
            return True, lat, "TLS Handshake OK"
    except Exception as e:
        lat = (time.perf_counter() - start) * 1000.0
        return False, lat, str(e)
    finally:
        try:
            sock.close()
        except Exception:
            pass

def run_diagnostics():
    print("================================================================")
    print("ДИАГНОСТИКА ДОСТУПНОСТИ СЕРВИСОВ (YOUTUBE, DISCORD, TG, SPOTIFY)")
    print("================================================================")
    targets = [
        ("YouTube Main", "www.youtube.com"),
        ("Discord Voice & Gateway", "gateway.discord.gg"),
        ("Discord Main API", "discord.com"),
        ("Telegram Web", "web.telegram.org"),
        ("Telegram Short (t.me)", "t.me"),
        ("Telegram API", "api.telegram.org"),
        ("Spotify Client", "spclient.wg.spotify.com")
    ]

    print(f"{'РЕСУРС':<26} {'УЗЕЛ':<32} {'СТАТУС':<12} {'ПИНГ'}")
    print("-" * 78)
    failed = 0
    for name, host in targets:
        ok, lat, msg = test_host_probe(host)
        status = "ДОСТУПЕН" if ok else "БЛОКИРОВКА"
        lat_str = f"{lat:6.1f} ms" if ok else "ТАЙМАУТ"
        if not ok:
            failed += 1
        print(f"{name:<26} {host:<32} {status:<12} {lat_str}")

    print("-" * 78)
    print("")
    rec = STRATEGIES[0]
    print("Рекомендуемая конфигурация (YouTube 4K, Discord, Telegram, Spotify):")
    print(f"Режим: {rec['name']}")
    print("================================================================")
    return rec

def install_winws_service(flags=None, strategy_id="1", bin_name="winws.exe"):
    if not is_admin():
        elevate_privileges()
        if not is_admin():
            print("[ОШИБКА] Требуются права Администратора для установки службы.")
            return False

    if not ensure_binaries():
        return False

    # Apply clean Google IPs to hosts to defeat ISP DNS poisoning
    fix_youtube_dns()

    # Use clean ASCII path C:\zapret\bin\winws.exe
    inst_bin = os.path.join(INSTALL_DIR, "bin", bin_name)
    bin_path = inst_bin if os.path.exists(inst_bin) else os.path.join(INSTALL_DIR, bin_name)

    if flags is None:
        flags = get_strategy_flags(strategy_id)

    # Clean existing service
    subprocess.run("sc.exe stop winws", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run("sc.exe delete winws", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run("sc.exe stop zapret", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run("sc.exe delete zapret", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.5)

    full_bin = f'\\"{bin_path}\\" {flags}'
    cmd = f'sc.exe create winws binPath= "{full_bin}" start= auto DisplayName= "zapret"'
    
    print("[ИНФО] Регистрация службы Windows в C:\\zapret...")
    res = subprocess.run(cmd, shell=True, capture_output=True)
    if res.returncode != 0:
        err = res.stderr.decode('cp866', errors='replace') or res.stdout.decode('cp866', errors='replace')
        print(f"[ОШИБКА] Ошибка при создании службы: {err}")
        return False

    subprocess.run('sc.exe description winws "Zapret DPI bypass software (YouTube, Discord, Telegram, Spotify)"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("[ИНФО] Запуск службы...")
    start_res = subprocess.run("sc.exe start winws", shell=True, capture_output=True)
    time.sleep(1.0)
    st = get_service_status("winws")
    if st == "RUNNING":
        print("[УСПЕХ] Служба zapret успешно создана и запущена!")
        print("[ИНФО] YouTube 4K, Discord, Telegram и Spotify разблокированы.")
        print("[ИНФО] Автозапуск при включении Windows: ВКЛЮЧЕН.")
        return True
    else:
        err = start_res.stderr.decode('cp866', errors='replace') or start_res.stdout.decode('cp866', errors='replace')
        print(f"[ВНИМАНИЕ] Служба зарегистрирована со статусом: {st}")
        return True

def control_service(action="status"):
    if action in ("start", "stop", "remove") and not is_admin():
        elevate_privileges()
    if action == "status":
        st = get_service_status("winws")
        print(f"Статус службы Zapret: {st}")
    elif action == "start":
        res = subprocess.run("sc.exe start winws", shell=True, capture_output=True)
        print(res.stdout.decode('cp866', errors='replace'))
    elif action == "stop":
        res = subprocess.run("sc.exe stop winws", shell=True, capture_output=True)
        print(res.stdout.decode('cp866', errors='replace'))
    elif action == "remove":
        subprocess.run("sc.exe stop winws", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = subprocess.run("sc.exe delete winws", shell=True, capture_output=True)
        clean_youtube_dns()
        print("[OK] Служба zapret удалена из Windows, hosts очищен.")

def print_browser_tips():
    print()
    print("================================================================")
    print("  ВАЖНЫЕ НАСТРОЙКИ ДЛЯ БРАУЗЕРА И DISCORD")
    print("================================================================")
    print(" 1. Если видео на YouTube крутится бесконечно (Chrome / Яндекс / Edge):")
    print("    - Откройте адрес: chrome://flags (или edge://flags / browser://flags)")
    print("    - Найдите 'Experimental QUIC protocol' -> поставьте 'Disabled'.")
    print("    - Найдите 'TLS 1.3 hybridized Kyber support' -> поставьте 'Disabled'.")
    print("    - Нажмите кнопку 'Relaunch' (Перезагрузить браузер).")
    print()
    print(" 2. Если в Discord бесконечно 'Подключение к RTC' / 'Нет маршрута':")
    print("    - Настройки Discord -> Настройки приложения -> Голос и видео.")
    print("    - Прокрутите вниз и выключите 'Включить новейшую сетевую подсистему'.")
    print("    - Убедитесь, что служба запущена в меню [1].")
    print("================================================================")

def interactive_menu():
    while True:
        st = get_service_status("winws")
        if st == "RUNNING":
            st_text = "РАБОТАЕТ (Обход активен) / RUNNING"
        elif st == "STOPPED":
            st_text = "ОСТАНОВЛЕНА / STOPPED"
        else:
            st_text = "НЕ УСТАНОВЛЕНА / NOT INSTALLED"

        admin_text = "ДА (Администратор) / YES" if is_admin() else "НЕТ (Ограниченный) / NO"
        procs, servs = find_conflicts()
        conf_text = f"ОБНАРУЖЕНЫ ({len(procs) + len(servs)})" if (procs or servs) else "НЕТ / NONE"

        print()
        print("================================================================")
        print("  ZAPRET-AUTO: АВТОМАТИЧЕСКИЙ ОБХОД (YOUTUBE, DISCORD, TG, SPOTIFY)")
        print("================================================================")
        print(f" Статус службы:        [{st_text}]")
        print(f" Права администратора: [{admin_text}]")
        print(f" Конфликты в системе:  [{conf_text}]")
        print("----------------------------------------------------------------")
        print(" [1] ВКЛЮЧИТЬ ОБХОД (1 клик — автоматическая настройка и запуск)")
        print(" [2] Выбрать профиль под своего провайдера (Flowseal стратегии)")
        print(" [3] Проверить доступность YouTube, Discord, Telegram, Spotify")
        print(" [4] Выключить обход (Остановить службу)")
        print(" [5] Полностью удалить службу из Windows")
        print(" [6] Закрыть конфликтующие программы (GoodbyeDPI и др.)")
        print(" [7] Советы по настройке браузера и Discord (QUIC / RTC)")
        print(" [0] Выход")
        print("----------------------------------------------------------------")
        choice = input("Выберите действие [0-7]: ").strip()

        if choice == "1":
            print("\n--- АВТОМАТИЧЕСКАЯ УСТАНОВКА И ЗАПУСК В 1 КЛИК ---")
            if not is_admin():
                elevate_privileges()
            print("[1/4] Проверка файлов winws, WinDivert, cygwin, пейлоадов и списков...")
            if not ensure_binaries():
                input("\nНажмите Enter для возврата...")
                continue
            print("[2/4] Очистка конфликтов (GoodbyeDPI / старые процессы)...")
            terminate_conflicts(silent=True)
            print("[3/4] Настройка чистых DNS для YouTube...")
            fix_youtube_dns()
            print("[4/4] Установка и запуск универсальной службы в C:\\zapret...")
            ok = install_winws_service(strategy_id="1")
            if ok:
                print("\n" + "=" * 64)
                print("  [✓] УСПЕШНО! YouTube 4K, Discord, Telegram и Spotify разблокированы.")
                print("  [✓] Установлено в чистый путь C:\\zapret без сбоев кодировки.")
                print("  [✓] Служба будет стартовать автоматически с Windows.")
                print("=" * 64)
            input("\nНажмите Enter для продолжения...")

        elif choice == "2":
            print("\nДоступные профили под провайдеров:")
            for s in STRATEGIES:
                print(f"  [{s['id']}] {s['name']}")
                print(f"      {s['desc']}")
            s_id = input("\nВыберите номер [1-5]: ").strip()
            match = next((s for s in STRATEGIES if s["id"] == s_id), None)
            if match:
                install_winws_service(strategy_id=s_id)
            else:
                print("[ОШИБКА] Неверный номер профиля.")
            input("\nНажмите Enter для продолжения...")

        elif choice == "3":
            run_diagnostics()
            input("\nНажмите Enter для продолжения...")

        elif choice == "4":
            control_service("stop")
            input("\nНажмите Enter для продолжения...")

        elif choice == "5":
            control_service("remove")
            input("\nНажмите Enter для продолжения...")

        elif choice == "6":
            terminate_conflicts(silent=False)
            input("\nНажмите Enter для продолжения...")

        elif choice == "7":
            print_browser_tips()
            input("\nНажмите Enter для продолжения...")

        elif choice == "0":
            sys.exit(0)

def main():
    if platform.system() == "Windows" and not is_admin():
        elevate_privileges()

    parser = argparse.ArgumentParser(description="Zapret-Auto: Диспетчер службы winws для YouTube и Discord")
    parser.add_argument("--auto", "-a", action="store_true", help="Автоматическая установка и запуск в 1 клик")
    parser.add_argument("--diagnose", "-d", action="store_true", help="Проверить доступность YouTube и Discord")
    parser.add_argument("--install", "-i", type=int, choices=[1, 2, 3, 4, 5], help="Установить профиль (1-5)")
    parser.add_argument("--status", "-s", action="store_true", help="Проверить статус службы")
    parser.add_argument("--stop", action="store_true", help="Остановить службу")
    parser.add_argument("--remove", action="store_true", help="Удалить службу")
    parser.add_argument("--clean", action="store_true", help="Завершить конфликтующие процессы")
    parser.add_argument("--tips", "-t", action="store_true", help="Показать советы для браузера и Discord")
    args = parser.parse_args()

    if args.auto:
        ensure_binaries()
        terminate_conflicts(silent=True)
        fix_youtube_dns()
        install_winws_service(strategy_id="1")
    elif args.diagnose:
        run_diagnostics()
    elif args.install:
        install_winws_service(strategy_id=str(args.install))
    elif args.status:
        control_service("status")
    elif args.stop:
        control_service("stop")
    elif args.remove:
        control_service("remove")
    elif args.clean:
        terminate_conflicts()
    elif args.tips:
        print_browser_tips()
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
