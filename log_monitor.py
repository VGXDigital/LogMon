#!/usr/bin/env python3
"""
Log Monitor Script v1.0
Monitors log files for errors and sends notifications when issues are detected.

VGX Consulting - Log Monitoring Solution
Copyright (c) 2026 VGX Consulting. All rights reserved.

This is proprietary software. Unauthorized copying, modification, distribution,
or use of this software is strictly prohibited.
"""

import os
import re
import ssl
import time
import smtplib
import argparse
import configparser
import concurrent.futures
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any, Optional

__version__ = "1.3.2"


class LogMonitor:
    error_patterns = [
        r'error', r'fail', r'exception', r'traceback', r'critical',
        r'fatal', r'warning', r'not found', r'permission denied',
        r'connection refused', r'timeout', r'unable to', r'could not',
        r'exit code', r'returned non-zero', r'aborted', r'killed'
    ]

    def __init__(self, debug: bool = False):
        """Initialize the LogMonitor."""
        self.debug = debug
        if self.debug:
            print("=" * 60)
            print("VGX Log Monitor - Debug Mode")
            print(f"Run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

        self._configure()
        self.compiled_pattern = re.compile('|'.join(self.error_patterns), re.IGNORECASE)

        if self.debug:
            self._print_debug_info()
            self.notification_file.parent.mkdir(parents=True, exist_ok=True)
            self.notification_file.touch(exist_ok=True)

    def _configure(self) -> None:
        """Load configuration from file and environment."""
        config = configparser.ConfigParser()
        config_file = Path.cwd() / 'log_monitor.conf'
        if config_file.exists():
            config.read(config_file)

        # Path settings
        self.log_dir = Path(os.getenv('VGX_LM_LOG_DIR') or config.get('Paths', 'log_dir', fallback=Path.home() / 'logs'))
        script_dir = Path(__file__).parent.resolve()
        writable_dir = self._get_writable_directory(script_dir)
        self.notification_file = Path(config.get('Paths', 'notification_file', fallback=writable_dir / 'notifications.log'))
        self.last_check_file = Path(config.get('Paths', 'last_check_file', fallback=writable_dir / '.last_check'))

        # SMTP settings
        self.smtp_server = os.getenv('VGX_LM_SMTP_SERVER') or config.get('SMTP', 'server', fallback=None)
        self.smtp_port = int(os.getenv('VGX_LM_SMTP_PORT') or config.get('SMTP', 'port', fallback=465))
        self.smtp_username = os.getenv('VGX_LM_SMTP_USERNAME') or config.get('SMTP', 'username', fallback=None)
        self.smtp_password = os.getenv('VGX_LM_SMTP_PASSWORD') or config.get('SMTP', 'password', fallback=None)
        self.smtp_from_email = os.getenv('VGX_LM_SMTP_FROM') or config.get('SMTP', 'from_email', fallback=None)
        self.smtp_to_email = os.getenv('VGX_LM_SMTP_TO') or config.get('SMTP', 'to_email', fallback=None)

    def _print_debug_info(self) -> None:
        """Print debug information."""
        print("Monitoring with combined regex pattern")
        print(f"Log directory: {self.log_dir}")
        print(f"State directory: {self.last_check_file.parent}")
        print(f"Notification file: {self.notification_file}")
        print(f"Last check file: {self.last_check_file}")
        print(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
        print(f"SMTP From: {self.smtp_from_email}")
        print(f"SMTP To: {self.smtp_to_email}")
        print(f"SMTP Username: {self.smtp_username}")

    def _get_writable_directory(self, preferred_dir: Path) -> Path:
        """Determine writable directory for state files."""
        test_file = preferred_dir / '.write_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
            return preferred_dir
        except (OSError, IOError):
            fallback_dir = Path('/tmp/vgx.logmonitor')
            fallback_dir.mkdir(exist_ok=True)
            return fallback_dir

    def get_log_files(self) -> List[Path]:
        """Get all .log files recursively in log_dir, excluding notification file."""
        if not self.log_dir.exists():
            if self.debug:
                print(f"WARNING: Log directory does not exist: {self.log_dir}")
            return []

        log_files = list(self.log_dir.rglob('*.log'))
        # Exclude the notification file to avoid scanning itself
        filtered_files = [f for f in log_files if f.resolve() != self.notification_file.resolve()]

        if self.debug:
            print(f"\nFound {len(filtered_files)} log file(s) to monitor:")
            for f in filtered_files:
                print(f"  - {f}")

        return filtered_files

    def get_last_check_time(self) -> float:
        """Get the timestamp of the last check from file."""
        if self.last_check_file.exists():
            try:
                return float(self.last_check_file.read_text().strip())
            except ValueError:
                return 0
        return 0

    def set_last_check_time(self, timestamp: float) -> None:
        """Save the timestamp of the current check."""
        self.last_check_file.write_text(str(timestamp))

    def find_errors_in_file(self, filepath: Path, since_timestamp: float) -> List[Dict[str, Any]]:
        """Find errors in a specific file since the last check."""
        try:
            if filepath.stat().st_mtime < since_timestamp:
                return []
        except OSError:
            return []

        errors = []
        try:
            with filepath.open('r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if self.compiled_pattern.search(line):
                        errors.append({
                            'file': str(filepath),
                            'line_number': i,
                            'line_content': line.strip(),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
        except Exception as e:
            if self.debug:
                self.log_notification(f"Error reading file {filepath}: {e}")

        return errors

    def scan_all_logs(self) -> List[Dict[str, Any]]:
        """Scan all log files for errors using a thread pool."""
        current_time = time.time()
        last_check = self.get_last_check_time()

        if last_check == 0:
            last_check = current_time - 3600
            if self.debug:
                print("\nFirst run detected - scanning last hour of logs")
        
        if self.debug:
            last_check_time = datetime.fromtimestamp(last_check).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nLast check: {last_check_time}")
            print("\nScanning log files for errors...")

        all_errors: List[Dict[str, Any]] = []
        log_files = self.get_log_files()

        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_file = {executor.submit(self.find_errors_in_file, log_file, last_check): log_file for log_file in log_files}
            for future in concurrent.futures.as_completed(future_to_file):
                log_file = future_to_file[future]
                try:
                    errors = future.result()
                    if errors:
                        if self.debug:
                            print(f"    Found {len(errors)} error(s) in {log_file}")
                        all_errors.extend(errors)
                except Exception as exc:
                    if self.debug:
                        print(f"{log_file} generated an exception: {exc}")

        self.set_last_check_time(current_time)

        if self.debug:
            print(f"\nTotal errors found: {len(all_errors)}")

        return all_errors

    def log_notification(self, message: str) -> None:
        """Log notification to file (only in debug mode)."""
        if not self.debug:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        try:
            with self.notification_file.open('a') as f:
                f.write(log_entry)
        except (OSError, IOError) as e:
            print(f"Warning: Could not write to notification file: {e}")

    def send_notification(self, errors: List[Dict[str, Any]]) -> None:
        """Send notifications about detected errors."""
        if not errors:
            return

        error_count = len(errors)
        
        # Log to notification file
        self.log_notification(f"Detected {error_count} errors")

        # Send email notification
        self.send_email_notification(errors)

    def _create_html_email(self, errors: List[Dict[str, Any]]) -> str:
        """Create an HTML formatted email body."""
        error_count = len(errors)
        
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: sans-serif; }}
                    h1 {{ color: #d9534f; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Log Monitor Alert: {error_count} error(s) detected</h1>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <table>
                    <tr>
                        <th>File</th>
                        <th>Line</th>
                        <th>Content</th>
                        <th>Timestamp</th>
                    </tr>
        """

        for error in errors:
            html += f"""
                    <tr>
                        <td>{error['file']}</td>
                        <td>{error['line_number']}</td>
                        <td><code>{error['line_content']}</code></td>
                        <td>{error['timestamp']}</td>
                    </tr>
            """

        html += """
                </table>
            </body>
        </html>
        """
        return html

    def send_email_notification(self, errors: List[Dict[str, Any]]) -> None:
        """Send email notification via SMTP."""
        error_count = len(errors)
        try:
            if self.debug:
                print("\nAttempting to send email notification...")
                print(f"  SMTP Server: {self.smtp_server}:{self.smtp_port}")
                print(f"  From: {self.smtp_from_email}")
                print(f"  To: {self.smtp_to_email}")
                print(f"  Username: {self.smtp_username}")

            if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.smtp_from_email, self.smtp_to_email]):
                raise ValueError("Missing SMTP configuration. Please check your config file or environment variables.")

            msg = MIMEMultipart()
            msg['From'] = self.smtp_from_email
            msg['To'] = self.smtp_to_email
            msg['Subject'] = f"Log Monitor Alert: {error_count} errors detected"
            
            html_body = self._create_html_email(errors)
            msg.attach(MIMEText(html_body, 'html'))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_from_email, self.smtp_to_email, msg.as_string())

            if self.debug:
                print(f"  ✓ Email sent successfully to {self.smtp_to_email}")
            self.log_notification(f"Email sent to {self.smtp_to_email}")

        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            if self.debug:
                print(f"  ✗ {error_msg}")
            self.log_notification(error_msg)

    def run(self) -> None:
        """Main method to run the log monitor."""
        if self.debug:
            print("\n" + "=" * 60)
            print("Starting log scan...")
            print("=" * 60)

        errors = self.scan_all_logs()

        if errors:
            self.send_notification(errors)
        elif self.debug:
            print("\n✓ No errors found - all clear!")

        if self.debug:
            print("\n" + "=" * 60)
            print("Log monitor completed")
            print(f"Run finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)


def main():
    """Main function to run the log monitor."""
    parser = argparse.ArgumentParser(
        description='Monitor log files for errors and send notifications',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with detailed logging to notification file')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    try:
        monitor = LogMonitor(debug=args.debug)
        monitor.run()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
