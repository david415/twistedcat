
from twisted.internet import protocol
from twisted.protocols.portforward import Proxy, ProxyClient
from twisted.internet.interfaces import IStreamClientEndpoint, IStreamServerEndpoint


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



class EndpointCrossOver(object):

    def __init__(self, endpoint1, endpoint2, handleError=None):
        self.endpoint1 = endpoint1
        self.endpoint2 = endpoint2
        self.handleError = handleError

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
