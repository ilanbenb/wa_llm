import asyncio
import logging
from asyncio.streams import StreamReader
from asyncio.subprocess import PIPE, Process
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class WhatsAppConfig:
    """Configuration class for WhatsApp process.

    Attributes:
        port: Port number for the WhatsApp process to listen on.
        webhook_url: URL where webhook events will be sent.
        webhook_secret: Secret key for webhook security.
        debug: Enable debug logging if True.
        os_name: Operating system name for the WhatsApp process.
        basic_auth: Basic authentication credentials in format "username:password".
        autoreply: Automatic reply message configuration.
        account_validation: Enable account validation if True.
        db_uri: Database connection URI.

    Example:
        ```python
        config = WhatsAppConfig(
            port=8080,
            webhook_url="http://localhost:8000/webhook",
            webhook_secret="your-secret-key",
            debug=True,
            basic_auth="admin:password123",
            db_uri="postgres://user:pass@localhost:5432/whatsapp"
        )
        ```
    """

    port: int
    webhook_url: str
    webhook_secret: str
    debug: bool = False
    os_name: str = "Chrome"
    basic_auth: Optional[str] = None
    autoreply: Optional[str] = None
    account_validation: bool = True
    db_uri: str = "file:storages/whatsapp.db?_foreign_keys=off"


class WhatsAppManager:
    """Manages a WhatsApp process asynchronously.

    This class handles starting, monitoring, and stopping a WhatsApp process.
    It provides automatic restart capabilities and proper resource cleanup.

    Args:
        config: WhatsAppConfig instance containing process configuration.
        whatsapp_binary_path: Path to the WhatsApp binary executable.
        max_restarts: Maximum number of restart attempts on process failure.
        restart_delay: Delay in seconds between restart attempts.

    Attributes:
        process: Current WhatsApp subprocess instance.
        restart_count: Number of restart attempts made.
        should_run: Flag indicating if the process should be running.
        logger: Logger instance for the manager.

    Example:
        ```python
        import asyncio
        from pathlib import Path

        async def main():
            # Create configuration
            config = WhatsAppConfig(
                port=8080,
                webhook_url="http://localhost:8000/webhook",
                webhook_secret="your-secret-key",
                debug=True
            )

            # Using context manager (recommended)
            async with WhatsAppManager(config) as manager:
                try:
                    # Your application logic here
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass

            # Or manual management
            manager = WhatsAppManager(
                config,
                whatsapp_binary_path="./whatsapp",
                max_restarts=3
            )
            await manager.start()
            try:
                # Your application logic here
                await asyncio.sleep(infinity)
            finally:
                await manager.stop()

        if __name__ == "__main__":
            asyncio.run(main())
        ```
    """

    def __init__(
        self,
        config: WhatsAppConfig,
        whatsapp_binary_path: str = "./whatsapp",
        max_restarts: int = 3,
        restart_delay: float = 5.0,
    ) -> None:
        self.config = config
        self.binary_path = Path(whatsapp_binary_path)
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay

        self.process: Optional[Process] = None
        self.restart_count: int = 0
        self.should_run: bool = False
        self._startup_lock: asyncio.Lock = asyncio.Lock()
        self._monitor_task: Optional[asyncio.Task[None]] = None

        self.logger: logging.Logger = logging.getLogger("WhatsAppManager")

    def _build_command(self) -> List[str]:
        """Build the command list with all configured flags.

        Constructs a list of command-line arguments based on the current configuration.

        Returns:
            List of strings representing the complete command with all flags.

        Example:
            ```python
            manager = WhatsAppManager(config)
            cmd = manager._build_command()
            # cmd = ['./whatsapp', '--port', '8080', '--debug=true', ...]
            ```
        """
        cmd = [str(self.binary_path)]

        if self.config.port:
            cmd.extend(["--port", str(self.config.port)])

        if self.config.debug:
            cmd.append("--debug=true")

        if self.config.os_name:
            cmd.extend(["--os", self.config.os_name])

        if self.config.basic_auth:
            cmd.extend(["--basic-auth", self.config.basic_auth])

        if self.config.autoreply:
            cmd.extend(["--autoreply", self.config.autoreply])

        if self.config.webhook_url:
            cmd.extend(["--webhook", self.config.webhook_url])

        if self.config.webhook_secret:
            cmd.extend(["--webhook-secret", self.config.webhook_secret])

        if self.config.account_validation:
            cmd.append("--account-validation=true")

        if self.config.db_uri:
            cmd.extend(["--db-uri", self.config.db_uri])

        return cmd

    async def _start_process(self) -> None:
        """Start the WhatsApp process with the configured parameters.

        Creates a new subprocess with the configured parameters and starts
        monitoring its output streams.

        Raises:
            OSError: If the binary file doesn't exist or isn't executable.
            Exception: If the process fails to start for any other reason.
        """
        cmd = self._build_command()

        self.logger.info(f"Starting WhatsApp process with command: {' '.join(cmd)}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd, stdout=PIPE, stderr=PIPE
            )

            if self.process.stdout is not None:
                asyncio.create_task(self._monitor_output(self.process.stdout, "stdout"))
            if self.process.stderr is not None:
                asyncio.create_task(self._monitor_output(self.process.stderr, "stderr"))

            # Start the process monitor
            self._monitor_task = asyncio.create_task(self._monitor_process())

        except Exception as e:
            self.logger.error(f"Failed to start WhatsApp process: {e}")
            raise

    async def _monitor_output(self, stream: StreamReader, name: str) -> None:
        """Monitor process output streams and log them.

        Args:
            stream: The output stream to monitor (stdout or stderr).
            name: Name of the stream for logging purposes.

        Example:
            ```python
            # Inside the class
            if self.process.stdout:
                await self._monitor_output(self.process.stdout, "stdout")
            ```
        """
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                self.logger.info(f"[{name}] {line.decode().strip()}")
        except Exception as e:
            self.logger.error(f"Error monitoring {name}: {e}")

    async def start(self) -> None:
        """Start the WhatsApp process and begin monitoring it.

        This method is thread-safe and will prevent multiple simultaneous
        start attempts. It initializes the process and begins monitoring it
        for failures.

        Raises:
            RuntimeError: If the process is already running.
        """
        async with self._startup_lock:
            if self.should_run:
                raise RuntimeError("Process is already running")

            self.should_run = True
            self.restart_count = 0
            await self._start_process()

    async def _monitor_process(self) -> None:
        """Monitor the process and handle restarts if necessary.

        Continuously monitors the process and attempts to restart it if it fails,
        up to the configured maximum number of restart attempts.
        """
        while self.should_run and self.process is not None:
            try:
                returncode = await self.process.wait()
                if returncode != 0 and self.should_run:
                    self.logger.warning(f"Process exited with code {returncode}")

                    if self.restart_count < self.max_restarts:
                        self.restart_count += 1
                        self.logger.info(
                            f"Restarting process (attempt {self.restart_count}/{self.max_restarts})"
                        )
                        await asyncio.sleep(self.restart_delay)
                        await self._start_process()
                    else:
                        self.logger.error("Max restart attempts reached")
                        self.should_run = False

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring process: {e}")

            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the WhatsApp process gracefully.

        Attempts to terminate the process gracefully, waiting for up to 5 seconds
        before forcing termination. Cleans up all resources afterwards.

        Example:
            ```python
            manager = WhatsAppManager(config)
            await manager.start()
            # ... some time later ...
            await manager.stop()  # Gracefully stops the process
            ```
        """
        self.should_run = False

        if self.process is not None:
            self.logger.info("Stopping WhatsApp process...")

            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Process did not terminate gracefully, forcing...")
                self.process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping process: {e}")
            finally:
                if self._monitor_task is not None:
                    self._monitor_task.cancel()
                    try:
                        await self._monitor_task
                    except asyncio.CancelledError:
                        pass
                    self._monitor_task = None

                self.process = None
                self.restart_count = 0

    async def __aenter__(self) -> "WhatsAppManager":
        """Async context manager entry.

        Returns:
            Self reference for use in context manager.
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit.

        Ensures proper cleanup of resources when exiting the context manager.

        Args:
            exc_type: Type of the exception that occurred, if any.
            exc_val: Value of the exception that occurred, if any.
            exc_tb: Traceback of the exception that occurred, if any.
        """
        await self.stop()
