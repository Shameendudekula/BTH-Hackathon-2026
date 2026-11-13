import socket
import unittest
from unittest.mock import patch
from launch import choose_port, healthy

class LaunchTests(unittest.TestCase):
    def test_skips_occupied_port(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port=sock.getsockname()[1]
            if port == 65535: self.skipTest('No next port')
            chosen=choose_port(port,20)
            self.assertGreater(chosen,port)
    def test_exhausted_port(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            with self.assertRaises(RuntimeError): choose_port(sock.getsockname()[1],1)
    def test_health_unavailable(self):
        with patch('urllib.request.OpenerDirector.open',side_effect=OSError('offline')):
            self.assertFalse(healthy('http://127.0.0.1:8501'))

if __name__=='__main__': unittest.main()
