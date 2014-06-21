#!/usr/bin/env python

from twisted.internet.endpoints import clientFromString, serverFromString
from twisted.internet import reactor, protocol
from twisted.protocols.portforward import Proxy, ProxyClient
import argparse
import sys

class ProxyEndpointProtocol(Proxy):

    def connectionMade(self):
        if self.factory.peerFactory.protocolInstance is None:
            self.transport.pauseProducing()
        else:
            self.peer.setPeer(self)

            self.transport.registerProducer(self.peer.transport, True)
            self.peer.transport.registerProducer(self.transport, True)

            self.peer.transport.resumeProducing()
        
class ProxyEndpointProtocolFactory(protocol.Factory):

    protocol = ProxyEndpointProtocol

    def __init__(self):
        self.peerFactory = None
        self.protocolInstance = None

    def setPeerFactory(self, peerFactory):
        self.peerFactory = peerFactory

    def buildProtocol(self, *args, **kw):
        self.protocolInstance = protocol.Factory.buildProtocol(self, *args, **kw)

        if self.peerFactory.protocolInstance is not None:
            self.protocolInstance.setPeer(self.peerFactory.protocolInstance)

        return self.protocolInstance


# twistedcat - twisted endpoint concatenator

def main():

    servers = None
    clients = None
    num_servers = 0

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', type=str, action="append", nargs='+', dest='server', help='server endpoint accumulator')
    parser.add_argument('client', action="append", nargs='*')
    args = parser.parse_args()

    if args.server is not None:
        num_servers += len(args.server)
        servers = map(lambda x:x[0], args.server)

    if num_servers + len(args.client[0]) != 2:
        parser.print_help()
        sys.exit(1)

    if len(args.client[0]) != 0:
        clients = args.client[0]

    if servers is not None and clients is not None:
        serverEndpointDescriptor = servers[0]
        clientEndpointDescriptor = clients[0]

        serverEndpoint = serverFromString(reactor, serverEndpointDescriptor)
        clientEndpoint = clientFromString(reactor, clientEndpointDescriptor)

        clientEndpointFactory = ProxyEndpointProtocolFactory()
        serverEndpointFactory = ProxyEndpointProtocolFactory()

        clientEndpointFactory.setPeerFactory(serverEndpointFactory)
        serverEndpointFactory.setPeerFactory(clientEndpointFactory)

        connectDeferred = clientEndpoint.connect(clientEndpointFactory)
        listeningPortDeferred = serverEndpoint.listen(serverEndpointFactory)
    elif servers is None and clients is not None:
        clientEndpointDescriptor1 = clients[0]
        clientEndpointDescriptor2 = clients[1]

        clientEndpoint1 = clientFromString(reactor, clientEndpointDescriptor1)
        clientEndpoint2 = clientFromString(reactor, clientEndpointDescriptor2)

        clientEndpointFactory1 = ProxyEndpointProtocolFactory()
        clientEndpointFactory2 = ProxyEndpointProtocolFactory()

        clientEndpointFactory1.setPeerFactory(clientEndpointFactory2)
        clientEndpointFactory2.setPeerFactory(clientEndpointFactory1)

        clientEndpoint1.connect(clientEndpointFactory1)
        clientEndpoint2.connect(clientEndpointFactory2)
    else:
        serverEndpointDescriptor1 = servers[0]
        serverEndpointDescriptor2 = servers[1]

        serverEndpoint1 = serverFromString(reactor, serverEndpointDescriptor1)
        serverEndpoint2 = serverFromString(reactor, serverEndpointDescriptor2)

        serverEndpointFactory1 = ProxyEndpointProtocolFactory()
        serverEndpointFactory2 = ProxyEndpointProtocolFactory()

        serverEndpointFactory1.setPeerFactory(serverEndpointFactory2)
        serverEndpointFactory2.setPeerFactory(serverEndpointFactory1)

        listeningPortDeferred1 = serverEndpoint1.listen(serverEndpointFactory1)
        listeningPortDeferred2 = serverEndpoint2.listen(serverEndpointFactory2)

    reactor.run()

if __name__ == '__main__':
    main()
