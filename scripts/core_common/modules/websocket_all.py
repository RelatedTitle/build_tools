#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join('..', '..'))
import config
import base
#import ixwebsocket
#import socketrocket
import socket_io

def make():
  #ixwebsocket.make()
  #socketrocket.make()
  socket_io.make()

  return
