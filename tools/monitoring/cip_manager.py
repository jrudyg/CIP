#!/usr/bin/env python
"""
CIP Manager - Process manager for Contract Intelligence Platform

Usage:
    python cip_manager.py start [backend|frontend|all]
    python cip_manager.py stop [backend|frontend|all]
    python cip_manager.py restart [backend|frontend|all]
    python cip_manager.py status
    python cip_manager.py logs [--follow]
"""

import argparse
import subprocess
import sys
import time
import signal
import os
import threading
import psutil
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import requests
from colorama import init, Fore, Style

from config import (
    PROCESS_CONFIGS, ProcessConfig,
    HEALTH_CHECK_TIMEOUT, GRACEFUL_SHUTDOWN_TIMEOUT,
    API_BASE_URL, HEALTH_ENDPOINT,
)

# Initialize colorama for Windows
init()


class ProcessState(Enum):
    """Process states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    CRASHED = "crashed"


@dataclass
class ProcessInfo:
    """Process information."""
    pid: Optional[int] = None
    state: ProcessState = ProcessState.STOPPED
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_error: Optional[str] = None


class ManagedProcess:
    """Wrapper for managed subprocess."""

    def __init__(self, config: ProcessConfig):
        self.config = config
        self.info = ProcessInfo()
        self._process: Optional[subprocess.Popen] = None
        self._output_thread: Optional[threading.Thread] = None
        self._running = False
        self._output_lines: List[str] = []
        self._max_output_lines = 100

    @property
    def state(self) -> ProcessState:
        return self.info.state

    @property
    def pid(self) -> Optional[int]:
        return self.info.pid

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.info.start_time and self.info.state == ProcessState.RUNNING:
            return datetime.now() - self.info.start_time
        return None

    def start(self) -> bool:
        """Start the process."""
        if self.info.state == ProcessState.RUNNING:
            return True

        self.info.state = ProcessState.STARTING
        self.info.last_error = None

        try:
            # Start process
            self._process = subprocess.Popen(
                self.config.command,
                cwd=str(self.config.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
            )

            self.info.pid = self._process.pid
            self.info.start_time = datetime.now()
            self.info.state = ProcessState.RUNNING
            self._running = True

            # Start output reader thread
            self._output_thread = threading.Thread(target=self._read_output, daemon=True)
            self._output_thread.start()

            # Wait for health check (if endpoint configured)
            if self.config.health_endpoint:
                time.sleep(2)
                if not self._check_health():
                    print(f"{Fore.YELLOW}  Warning: Health check not responding yet{Style.RESET_ALL}")

            return True

        except Exception as e:
            self.info.state = ProcessState.CRASHED
            self.info.last_error = str(e)
            return False

    def stop(self, timeout: int = GRACEFUL_SHUTDOWN_TIMEOUT) -> bool:
        """Stop the process."""
        if self.info.state == ProcessState.STOPPED:
            return True

        self.info.state = ProcessState.STOPPING
        self._running = False

        if self._process:
            try:
                # Try graceful shutdown first
                if os.name == 'nt':
                    self._process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self._process.terminate()

                try:
                    self._process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Force kill
                    self._process.kill()
                    self._process.wait(timeout=5)

            except Exception as e:
                self.info.last_error = str(e)

            self._process = None

        self.info.state = ProcessState.STOPPED
        self.info.pid = None
        return True

    def restart(self) -> bool:
        """Restart the process."""
        self.stop()
        time.sleep(1)
        self.info.restart_count += 1
        return self.start()

    def is_alive(self) -> bool:
        """Check if process is alive."""
        if self._process:
            return self._process.poll() is None
        return False

    def get_resource_usage(self) -> Dict:
        """Get CPU and memory usage."""
        if self.info.pid:
            try:
                proc = psutil.Process(self.info.pid)
                return {
                    'cpu_percent': proc.cpu_percent(),
                    'memory_mb': proc.memory_info().rss / (1024 * 1024),
                }
            except:
                pass
        return {'cpu_percent': 0, 'memory_mb': 0}

    def get_recent_output(self, lines: int = 20) -> List[str]:
        """Get recent output lines."""
        return self._output_lines[-lines:]

    def _read_output(self):
        """Read process output in background."""
        while self._running and self._process:
            try:
                line = self._process.stdout.readline()
                if line:
                    self._output_lines.append(line.rstrip())
                    if len(self._output_lines) > self._max_output_lines:
                        self._output_lines = self._output_lines[-self._max_output_lines:]
                elif self._process.poll() is not None:
                    # Process ended
                    break
            except:
                break

        # Check if crashed
        if self._running and self._process and self._process.poll() is not None:
            if self._process.returncode != 0:
                self.info.state = ProcessState.CRASHED
                self.info.last_error = f"Exit code {self._process.returncode}"

    def _check_health(self) -> bool:
        """Check health endpoint."""
        if not self.config.health_endpoint:
            return True
        try:
            resp = requests.get(self.config.health_endpoint, timeout=HEALTH_CHECK_TIMEOUT)
            return resp.ok
        except:
            return False


class ProcessManager:
    """Manage multiple CIP processes."""

    def __init__(self):
        self.processes: Dict[str, ManagedProcess] = {}
        self._setup_signal_handlers()

        # Register processes
        for name, config in PROCESS_CONFIGS.items():
            self.processes[name] = ManagedProcess(config)

    def start(self, name: str = None) -> bool:
        """Start process(es)."""
        if name and name != "all":
            if name not in self.processes:
                print(f"{Fore.RED}Unknown process: {name}{Style.RESET_ALL}")
                return False
            return self._start_one(name)
        else:
            return self._start_all()

    def stop(self, name: str = None) -> bool:
        """Stop process(es)."""
        if name and name != "all":
            if name not in self.processes:
                print(f"{Fore.RED}Unknown process: {name}{Style.RESET_ALL}")
                return False
            return self._stop_one(name)
        else:
            return self._stop_all()

    def restart(self, name: str = None) -> bool:
        """Restart process(es)."""
        if name and name != "all":
            if name not in self.processes:
                print(f"{Fore.RED}Unknown process: {name}{Style.RESET_ALL}")
                return False
            return self._restart_one(name)
        else:
            self._stop_all()
            time.sleep(2)
            return self._start_all()

    def status(self) -> Dict[str, Dict]:
        """Get status of all processes."""
        result = {}
        for name, proc in self.processes.items():
            usage = proc.get_resource_usage()
            result[name] = {
                'state': proc.state.value,
                'pid': proc.pid,
                'uptime': str(proc.uptime) if proc.uptime else None,
                'restart_count': proc.info.restart_count,
                'last_error': proc.info.last_error,
                'cpu_percent': usage['cpu_percent'],
                'memory_mb': usage['memory_mb'],
                'port': proc.config.port,
            }
        return result

    def _start_one(self, name: str) -> bool:
        """Start a single process."""
        proc = self.processes[name]
        print(f"Starting {name}...", end=" ", flush=True)
        if proc.start():
            print(f"{Fore.GREEN}OK{Style.RESET_ALL} (PID: {proc.pid})")
            return True
        else:
            print(f"{Fore.RED}FAILED{Style.RESET_ALL}")
            if proc.info.last_error:
                print(f"  Error: {proc.info.last_error}")
            return False

    def _stop_one(self, name: str) -> bool:
        """Stop a single process."""
        proc = self.processes[name]
        print(f"Stopping {name}...", end=" ", flush=True)
        if proc.stop():
            print(f"{Fore.GREEN}OK{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}FAILED{Style.RESET_ALL}")
            return False

    def _restart_one(self, name: str) -> bool:
        """Restart a single process."""
        proc = self.processes[name]
        print(f"Restarting {name}...", end=" ", flush=True)
        if proc.restart():
            print(f"{Fore.GREEN}OK{Style.RESET_ALL} (PID: {proc.pid})")
            return True
        else:
            print(f"{Fore.RED}FAILED{Style.RESET_ALL}")
            return False

    def _start_all(self) -> bool:
        """Start all processes."""
        success = True
        for name in self.processes:
            if not self._start_one(name):
                success = False
        return success

    def _stop_all(self) -> bool:
        """Stop all processes."""
        success = True
        for name in reversed(list(self.processes.keys())):
            if not self._stop_one(name):
                success = False
        return success

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def handler(signum, frame):
            print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
            self._stop_all()
            sys.exit(0)

        signal.signal(signal.SIGINT, handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, handler)


def print_status_table(status: Dict[str, Dict]):
    """Print status as a table."""
    print(f"\n{Fore.CYAN}{'SERVICE':<12} {'STATUS':<12} {'PID':<8} {'UPTIME':<12} {'CPU':<8} {'MEM':<10} {'PORT':<6}{Style.RESET_ALL}")
    print("-" * 70)

    for name, info in status.items():
        state = info['state']
        state_color = {
            'running': Fore.GREEN,
            'stopped': Fore.WHITE,
            'crashed': Fore.RED,
            'starting': Fore.YELLOW,
            'stopping': Fore.YELLOW,
        }.get(state, Fore.WHITE)

        pid = str(info['pid']) if info['pid'] else "-"
        uptime = info['uptime'].split('.')[0] if info['uptime'] else "-"
        cpu = f"{info['cpu_percent']:.1f}%" if info['cpu_percent'] else "-"
        mem = f"{info['memory_mb']:.1f}MB" if info['memory_mb'] else "-"
        port = str(info['port'])

        print(f"{name:<12} {state_color}{state:<12}{Style.RESET_ALL} {pid:<8} {uptime:<12} {cpu:<8} {mem:<10} {port:<6}")

    print()


def cmd_start(args, manager: ProcessManager):
    """Start command."""
    target = args.target or "all"
    print(f"\n{Fore.CYAN}Starting CIP services...{Style.RESET_ALL}\n")
    manager.start(target)
    print()
    print_status_table(manager.status())


def cmd_stop(args, manager: ProcessManager):
    """Stop command."""
    target = args.target or "all"
    print(f"\n{Fore.CYAN}Stopping CIP services...{Style.RESET_ALL}\n")
    manager.stop(target)
    print()
    print_status_table(manager.status())


def cmd_restart(args, manager: ProcessManager):
    """Restart command."""
    target = args.target or "all"
    print(f"\n{Fore.CYAN}Restarting CIP services...{Style.RESET_ALL}\n")
    manager.restart(target)
    print()
    print_status_table(manager.status())


def cmd_status(args, manager: ProcessManager):
    """Status command."""
    print(f"\n{Fore.CYAN}CIP Service Status{Style.RESET_ALL}")
    print_status_table(manager.status())

    # Check health endpoint
    try:
        resp = requests.get(HEALTH_ENDPOINT, timeout=3)
        if resp.ok:
            health = resp.json()
            print(f"{Fore.GREEN}Health Check: OK{Style.RESET_ALL}")
            print(f"  Orchestrator: {'Yes' if health.get('orchestrator') else 'No'}")
            print(f"  API Key: {'Configured' if health.get('api_key_configured') else 'Missing'}")
        else:
            print(f"{Fore.RED}Health Check: HTTP {resp.status_code}{Style.RESET_ALL}")
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}Health Check: Connection refused{Style.RESET_ALL}")
    except:
        print(f"{Fore.YELLOW}Health Check: Unable to connect{Style.RESET_ALL}")

    print()


def cmd_logs(args, manager: ProcessManager):
    """View combined logs."""
    print(f"\n{Fore.CYAN}Recent Output{Style.RESET_ALL}\n")

    for name, proc in manager.processes.items():
        output = proc.get_recent_output(args.lines)
        if output:
            print(f"{Fore.YELLOW}[{name}]{Style.RESET_ALL}")
            for line in output:
                print(f"  {line}")
            print()

    if args.follow:
        print(f"{Fore.YELLOW}Following logs... (Ctrl+C to stop){Style.RESET_ALL}\n")
        try:
            while True:
                for name, proc in manager.processes.items():
                    output = proc.get_recent_output(1)
                    if output:
                        print(f"{Fore.YELLOW}[{name}]{Style.RESET_ALL} {output[-1]}")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Stopped{Style.RESET_ALL}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CIP Manager - Process manager for Contract Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument(
        "target", nargs="?", choices=["backend", "frontend", "all"],
        default="all", help="Service to start (default: all)"
    )

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument(
        "target", nargs="?", choices=["backend", "frontend", "all"],
        default="all", help="Service to stop (default: all)"
    )

    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart services")
    restart_parser.add_argument(
        "target", nargs="?", choices=["backend", "frontend", "all"],
        default="all", help="Service to restart (default: all)"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show service status")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View combined logs")
    logs_parser.add_argument(
        "--follow", "-f", action="store_true",
        help="Follow log output"
    )
    logs_parser.add_argument(
        "--lines", "-n", type=int, default=20,
        help="Number of lines (default: 20)"
    )

    args = parser.parse_args()

    # Create manager
    manager = ProcessManager()

    # Default to status if no command
    if not args.command:
        cmd_status(args, manager)
        return

    # Dispatch command
    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "logs": cmd_logs,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args, manager)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
