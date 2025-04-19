#!/usr/bin/env python

import sys
sys.path.append('../..')
import config
import base
import os
import subprocess
import glob

def correct_namespace(dir):
  folder = dir
  if ("/" != folder[-1:]):
    folder += "/"
  folder += "*"
  for file in glob.glob(folder):
    if base.is_file(file):
      base.replaceInFile(file, "namespace sio", "namespace sio_no_tls")
      base.replaceInFile(file, "asio::", "asio_no_tls::")
      base.replaceInFile(file, "sio::", "sio_no_tls::")
      base.replaceInFile(file, "asio_no_tls::", "asio::")
    elif base.is_dir(file):
      correct_namespace(file)
  return

def make():
  base_dir = os.path.join(base.get_script_dir(), "../../core/Common/3dParty/socketio")
  if not base.is_dir(os.path.join(base_dir, "socket.io-client-cpp")):
    base.cmd_in_dir(base_dir, "git", ["clone", "https://github.com/socketio/socket.io-client-cpp.git"])
    base.cmd_in_dir(os.path.join(base_dir, "socket.io-client-cpp"), "git", ["checkout", "da779141a7379cc30c870d48295033bc16a23c66"])
    base.cmd_in_dir(os.path.join(base_dir, "socket.io-client-cpp"), "git", ["submodule", "init"])
    base.cmd_in_dir(os.path.join(base_dir, "socket.io-client-cpp"), "git", ["submodule", "update"])
    base.cmd_in_dir(os.path.join(base_dir, "socket.io-client-cpp/lib/asio"), "git", ["checkout", "230c0d2ae035c5ce1292233fcab03cea0d341264"])
    base.cmd_in_dir(os.path.join(base_dir, "socket.io-client-cpp/lib/websocketpp"), "git", ["checkout", "56123c87598f8b1dd471be83ca841ceae07f95ba"])
    # patches
    base.apply_patch(os.path.join(base_dir, "socket.io-client-cpp/lib/websocketpp/websocketpp/impl/connection_impl.hpp"), os.path.join(base_dir, "patches/websocketpp.patch"))
    base.apply_patch(os.path.join(base_dir, "socket.io-client-cpp/src/internal/sio_client_impl.cpp"), os.path.join(base_dir, "patches/sio_client_impl_fail.patch"))
    base.apply_patch(os.path.join(base_dir, "socket.io-client-cpp/src/internal/sio_client_impl.cpp"), os.path.join(base_dir, "patches/sio_client_impl_open.patch"))
    base.apply_patch(os.path.join(base_dir, "socket.io-client-cpp/src/internal/sio_client_impl.cpp"), os.path.join(base_dir, "patches/sio_client_impl_close_timeout.patch"))

    # no tls realization (remove if socket.io fix this)
    dst_dir = os.path.join(base_dir, "socket.io-client-cpp/src_no_tls")
    base.copy_dir(os.path.join(base_dir, "socket.io-client-cpp/src"), dst_dir)
    correct_namespace(dst_dir)
    base.replaceInFile(os.path.join(dst_dir, "internal/sio_client_impl.h"), "SIO_TLS", "SIO_TLS_NO")
    base.replaceInFile(os.path.join(dst_dir, "internal/sio_client_impl.cpp"), "SIO_TLS", "SIO_TLS_NO")

    base.replaceInFile(os.path.join(dst_dir, "sio_socket.h"), "SIO_SOCKET_H", "SIO_SOCKET_NO_TLS_H")
    base.replaceInFile(os.path.join(dst_dir, "sio_client.h"), "SIO_CLIENT_H", "SIO_CLIENT_NO_TLS_H")
    base.replaceInFile(os.path.join(dst_dir, "sio_message.h"), "__SIO_MESSAGE_H__", "__SIO_MESSAGE_NO_TLS_H__")
    base.replaceInFile(os.path.join(dst_dir, "internal/sio_packet.h"), "SIO_PACKET_H", "SIO_PACKET_NO_TLS_H")

    old_ping = "        m_ping_timeout_timer->expires_from_now(milliseconds(m_ping_interval + m_ping_timeout), ec);"
    new_ping = "#if defined(PING_TIMEOUT_INTERVAL)\n"
    new_ping += "        m_ping_timeout_timer->expires_from_now(milliseconds(PING_TIMEOUT_INTERVAL), ec);\n"
    new_ping += "#else\n"
    new_ping += old_ping
    new_ping += "\n#endif"

    base.replaceInFile(os.path.join(base_dir, "socket.io-client-cpp/src/internal/sio_client_impl.cpp"), old_ping, new_ping)
    base.replaceInFile(os.path.join(base_dir, "socket.io-client-cpp/src_no_tls/internal/sio_client_impl.cpp"), old_ping, new_ping)
  return
