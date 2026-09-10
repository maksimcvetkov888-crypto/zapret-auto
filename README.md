# zapret-auto

[Русский](#русский) | [English](#english)

---

## Русский

Автономный диспетчер службы `winws` (Zapret) для Windows с автоматической диагностикой провайдера и установкой службы в один клик.

Решает проблему постоянных блокировок и замедления **YouTube**, **Discord**, **Telegram** и **Spotify** на базе проверенных пресетов Flowseal (`zapret-discord-youtube`).

### Возможности

- **Экспресс-диагностика (~5 секунд)**: замер доступности узлов YouTube, Discord, Telegram и Spotify (`spclient.wg.spotify.com`, `t.me`).
- **Управление службой Windows**: установка `winws` в автозагрузку Windows (через `sc.exe`) в чистый путь `C:\zapret`.
- **Детектор конфликтов**: обнаружение и завершение зависших процессов `winws`, `goodbyedpi`, `byedpi` и освобождение заблокированного драйвера `WinDivert`.
- **5 проверенных пресетов Flowseal**:
  1. *General (Default)*: multisplit 4PDA + Google + Discord UDP fake (YouTube 4K, Discord, Telegram, Spotify).
  2. *General (ALT)*: фейковые TLS пакеты с временными метками TCP (Ростелеком, Дом.ру, МТС).
  3. *General (ALT2)*: multisplit pos 2 seqovl 652 для строгой фильтрации ТСПУ.
  4. *General (FAKE TLS AUTO)*: dynamic multidisorder с подменой SNI и сессионных ID (Билайн, Мегафон, Tele2).
  5. *General (SIMPLE FAKE)*: облегченный hostfakesplit TS.
- Интерактивное терминальное меню в стиле Zapret.
- Работает без внешних зависимостей (чистый Python, компилируется в автономный `.exe`).

### Быстрый старт

#### Windows
Запустите `run.bat` (от имени Администратора) или выполните:
```cmd
python zapret_auto.py
```

#### Команды CLI
```bash
# Автоматическая настройка и запуск в 1 клик
python zapret_auto.py --auto

# Диагностика и автоподбор стратегии
python zapret_auto.py --diagnose

# Установить стратегию №2 в службу Windows
python zapret_auto.py --install 2

# Проверить статус службы
python zapret_auto.py --status

# Очистить конфликтующие процессы и освободить WinDivert
python zapret_auto.py --clean

# Остановить / удалить службу
python zapret_auto.py --stop
python zapret_auto.py --remove
```

### Лицензия
MIT License.

---

## English

Zero-dependency Windows service dispatcher and automated DPI strategy optimizer for `winws` (Zapret).

Automatically resolves YouTube and Discord throttling by benchmarking and applying the optimal DPI bypass strategy for your ISP in a single click.

### Features

- **Rapid ISP Diagnostics (~5s)**: Probes YouTube (`googlevideo.com`) and Discord (`gateway.discord.gg`) to detect exact DPI filtering signatures and recommend the winning strategy.
- **Windows Service Automation**: Installs `winws` as an auto-starting Windows system service (via `sc.exe`).
- **Conflict Resolver**: Scans and kills stuck `winws`, `goodbyedpi`, or `byedpi` processes and cleans locked `WinDivert` driver instances.
- **5 Proven ISP Bypass Presets**:
  1. *General Fast Split*: Low-overhead 2-byte TLS ClientHello split.
  2. *Discord & YouTube Fake Disoob*: Fake packet injection with sequence desync for strict filters.
  3. *Autottl Hostcase Combo*: Low-TTL packets with checksum corruption.
  4. *Multi-split SNI Drop*: SNI fragmentation across middle domain boundary.
  5. *Aggressive Fake ClientHello*: Repeated fake injection for stateful firewalls.
- Interactive Zapret-style numbered terminal menu.
- Zero third-party dependencies.

### Quick Start

#### Windows
Run `run.bat` (as Administrator) or execute:
```cmd
python zapret_auto.py
```

#### CLI Commands
```bash
# 1-click automatic setup and service start
python zapret_auto.py --auto

# Run ISP diagnostic
python zapret_auto.py --diagnose

# Install preset strategy #2
python zapret_auto.py --install 2

# Check service status
python zapret_auto.py --status

# Clean conflicting tools & locked WinDivert
python zapret_auto.py --clean

# Stop or remove service
python zapret_auto.py --stop
python zapret_auto.py --remove
```

### License
MIT License.
