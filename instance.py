"""Single-instance control, so `python main.py --stop` can stop a running My-Woofie."""
import logging

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

log = logging.getLogger("woofie.instance")

SERVER_NAME = "my-woofie-companion"


def send_command(command, timeout_ms=500):
    """Send a command to a running My-Woofie. Returns True if an instance answered."""
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(timeout_ms):
        return False
    socket.write(command.encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(timeout_ms)
    socket.disconnectFromServer()
    return True


class InstanceServer(QObject):
    """Listens on a local (same-machine only) socket for short text commands such as 'quit'."""
    command_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = QLocalServer(self)
        QLocalServer.removeServer(SERVER_NAME)  # clear a stale socket left behind by a crash
        self.active = self._server.listen(SERVER_NAME)
        if not self.active:
            log.warning("Could not listen for control commands: %s", self._server.errorString())
        self._server.newConnection.connect(self._on_connection)

    def _on_connection(self):
        while self._server.hasPendingConnections():
            connection = self._server.nextPendingConnection()
            connection.waitForReadyRead(200)
            command = bytes(connection.readAll()).decode("utf-8", "ignore").strip()
            connection.disconnectFromServer()
            if command:
                log.info("Received command: %s", command)
                self.command_received.emit(command)
