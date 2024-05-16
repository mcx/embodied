import pathlib
import sys
import time

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

import embodied
from embodied import timer
import numpy as np


class TestBandwidth:

  def test_numpy_read(self):
    arr = np.ones((128, 1024, 1024), np.int64)  # 1 GiB
    size = arr.nbytes / (1024**3)
    for _ in range(10):
      with timer.section('step'):
        arr.sum()
    dt = timer.stats()['step/avg']
    print(f'numpy_read: {dt:.3f} avg | {size/dt:.2f} gib/s')

  def test_numpy_copy(self):
    arr = np.ones((1024, 1024, 1024), np.uint8)
    size = arr.nbytes / (1024**3)
    for _ in range(10):
      with timer.section('step'):
        arr.copy()
    dt = timer.stats()['step/avg']
    print(f'numpy_copy: {dt:.3f} avg | {size/dt:.2f} gib/s')

  def test_socket_send(self):
    shape, dtype, gib = (1024, 1024, 1024), np.uint8, 1.00

    def server(context, addr):
      server = embodied.distr.Server(addr)
      data = {'foo': np.ones(shape, dtype)}
      server.bind('function', lambda _: data)
      with server:
        while context.running:
          time.sleep(0.01)

    addr = f'tcp://localhost:{embodied.distr.get_free_port()}'
    proc = embodied.distr.StoppableProcess(server, addr, start=True)

    client = embodied.distr.Client(addr)
    client.connect()
    for _ in range(10):
      with timer.section('step'):
        client.function({}).result()
    proc.stop()

    dt = timer.stats()['step/avg']
    print(f'socket_send: {dt:.3f} avg | {gib/dt:.2f} gib/s')


if __name__ == '__main__':
  TestBandwidth().test_numpy_read()  # 21 gib/s
  TestBandwidth().test_numpy_copy()  # 7 gib/s
  TestBandwidth().test_socket_send()  # 4 gib/s
