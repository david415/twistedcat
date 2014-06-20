#!/usr/bin/env python

from twisted.internet.endpoints import clientFromString, serverFromString
from twisted.internet import reactor, protocol
from twisted.protocols.portforward import Proxy, ProxyClient


class ProxyClientEndpointFactory(protocol.Factory, object):

    protocol = ProxyClient

    def setServer(self, server):
        print "ProxyClientEndpointFactory.__init__"
        self.server = server

    def buildProtocol(self, *args, **kw):
        print "ProxyClientEndpointFactory.buildProtocol"
        prot = protocol.Factory.buildProtocol(self, *args, **kw)
        prot.setPeer(self.server)
        return prot

class ProxyServerEndpointProtocol(Proxy):
    """server endpoint to client endpoint proxy
    """
    clientEndpointProtocolFactory = ProxyClientEndpointFactory
    reactor = None

    def connectionMade(self):
        print "ProxyServerEndpointProtocol.connectionMade"
        # Don't read anything from the connecting client until we have
        # somewhere to send it to.
        self.transport.pauseProducing()
    
        self.client = self.clientEndpointProtocolFactory()
        self.client.setServer(self)

        if self.reactor is None:
            from twisted.internet import reactor
            self.reactor = reactor
        self.clientEndpoint = clientFromString(self.reactor, self.factory.clientEndpointDescriptor)
        self.connectDeferred = self.clientEndpoint.connect(self.client)
        self.connectDeferred.addErrback(lambda r: self.clientConnectionFailed(f, r))
                
    def clientConnectionFailed(self, factory, reason):
        print "ProxyServerEndpointProtocol.clientConnectionFailed %s %s" % (factory, reason)
        self.transport.loseConnection()

class ProxyServerEndpointProtocolFactory(protocol.Factory):

    protocol = ProxyServerEndpointProtocol

    def __init__(self, clientEndpointDescriptor):
        print "ProxyEndpointProtocolFactory.__init__"
        self.clientEndpointDescriptor = clientEndpointDescriptor


# twistedcat - endpoint plumber

def main():

    # client to server twisted endpoint proxy

    # TODO: parse commandline args instead of hardcoding
    serverEndpointDescriptor = 'stdio:'
    clientEndpointDescriptor = 'tcp:127.0.0.1:1666'

    serverEndpoint = serverFromString(reactor, serverEndpointDescriptor)
    serverProxyFactory = ProxyServerEndpointProtocolFactory(clientEndpointDescriptor)    
    listeningPortDeferred = serverEndpoint.listen(serverProxyFactory)

    # XXX
    #listeningPortDeferred.addCallback(serverProxyFactory.setListeningPort)

    def setup_complete(port):
        print "setup_complete %s" % port.getHost()
    def setup_failed(arg):
        print "SETUP FAILED", arg

    listeningPortDeferred.addCallback(setup_complete)
    listeningPortDeferred.addErrback(setup_failed)

    reactor.run()

if __name__ == '__main__':
    main()
