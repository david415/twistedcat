#!/usr/bin/env python

from twisted.internet.endpoints import clientFromString, serverFromString
from twisted.internet import reactor, protocol, defer
from twisted.internet.interfaces import IStreamClientEndpoint, IStreamServerEndpoint
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

    def connectionLost(self, reason):
        # XXX
        #self.peer.transport.loseConnection()
        self.transport.loseConnection()

        if self.factory.handleLostConnection is not None:
            self.factory.handleLostConnection()


class ProxyEndpointProtocolFactory(protocol.Factory):

    protocol = ProxyEndpointProtocol

    def __init__(self, handleLostConnection=None):
        self.peerFactory = None
        self.protocolInstance = None
        self.handleLostConnection = handleLostConnection

    def setPeerFactory(self, peerFactory):
        self.peerFactory = peerFactory

    def buildProtocol(self, *args, **kw):
        self.protocolInstance = protocol.Factory.buildProtocol(self, *args, **kw)

        if self.peerFactory.protocolInstance is not None:
            self.protocolInstance.setPeer(self.peerFactory.protocolInstance)

        return self.protocolInstance


def maybeClientFromString(reactor, endpointDescriptor):
    try:
        endpoint = clientFromString(reactor, endpointDescriptor)
    except TypeError, e:
        endpoint = None
    return endpoint

def maybeServerFromString(reactor, endpointDescriptor):
    try:
        endpoint = serverFromString(reactor, endpointDescriptor)
    except TypeError, e:
        endpoint = None
    return endpoint

class InvalidEndpointDescriptorError(Exception):
    """We cannot make a connection without valid endpoint descriptors"""

def endpointFromString(reactor, endpointDescriptor):
    endpoint = maybeClientFromString(reactor, endpointDescriptor)
    if endpoint is None:
        endpoint = maybeServerFromString(reactor, endpointDescriptor)
    if endpoint is None:
        raise InvalidEndpointDescriptorError()
    return endpoint


class EndpointCrossOver(object):

    def __init__(self, endpoint1, endpoint2, handleError=None):
        self.endpoint1 = endpoint1
        self.endpoint2 = endpoint2
        self.handleError = handleError

    def appendListeningPort(self, port):
        self.listeningPorts.append(port)

    def _openEndpoint(self, endpoint, factory):
        if IStreamClientEndpoint.providedBy(endpoint):
            d = endpoint.connect(factory)
        elif IStreamServerEndpoint.providedBy(endpoint):
            d = endpoint.listen(factory)
        else:
            raise ValueError('must provide either IStreamClientEndpoint or IStreamServerEndpoint')

    def join(self):
        self.factory1 = ProxyEndpointProtocolFactory(handleLostConnection=self.handleError)
        self.factory2 = ProxyEndpointProtocolFactory(handleLostConnection=self.handleError)

        self.factory1.setPeerFactory(self.factory2)
        self.factory2.setPeerFactory(self.factory1)

        self._openEndpoint(self.endpoint1, self.factory1)
        self._openEndpoint(self.endpoint2, self.factory2)


# twistedcat - twisted endpoint concatenator

def main():

    servers = None
    clients = None
    num_servers = 0

    parser = argparse.ArgumentParser()
    parser.add_argument('endpoints', action="append", nargs='*')
    args = parser.parse_args()

    if len(args.endpoints[0]) != 2:
        parser.print_help()
        sys.exit(1)

    def handle_error():
        if reactor.running:
            reactor.stop()

    endpoint_pipe = EndpointCrossOver(endpointFromString(reactor, args.endpoints[0][0]),
                                      endpointFromString(reactor, args.endpoints[0][1]),
                                      handleError=handle_error)
    endpoint_pipe.join()
    reactor.run()

if __name__ == '__main__':
    main()
