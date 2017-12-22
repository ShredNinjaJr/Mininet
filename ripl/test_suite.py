from mn import topos
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink

ls = topos['ft']()

net = Mininet(ls, controller=RemoteController, autoSetMacs=True)
net.start()

left = list()
right = list()
num_hosts = len(net.hosts)
i = 0
for h in net.hosts:
    if (i < num_hosts / 2):
        left.append(h)
    else:
        right.append(h)
    i += 1

for i in range(0, len(right)):
    right[i].sendCmd('iperf -s')

for i in range(0, len(left)):
    print('sending')
    cmd = 'iperf -c %s -t %d -i 1 -y C > %d.out' % (right[i].IP(), 5, i)
    left[i].sendCmd(cmd)
for i in range(0, len(left)):
    left[i].waitOutput()


net.stop()
