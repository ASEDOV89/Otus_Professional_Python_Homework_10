import sys
import socket
import time


def wait_for_db(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.connect((host, port))
            s.close()
            return
        except socket.error:
            time.sleep(1)


if __name__ == "__main__":
    host = sys.argv[1]
    port = int(sys.argv[2])
    wait_for_db(host, port)
