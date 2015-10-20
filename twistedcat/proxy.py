from twisted.protocols import basic
from twisted.internet import protocol, defer

ALLOWED = """
PROTOCOLINFO
250-PROTOCOLINFO 1
250-AUTH METHODS=COOKIE,SAFECOOKIE COOKIEFILE="/var/run/tor/control.authcookie"
250 OK
""".strip().split("\n")

ALLOWED_PREFIXES = """
650 BW
AUTHENTICATE
GETCONF BandwidthRate
250 BandwidthRate=
GETCONF BandwidthBurst
250 BandwidthBurst=
GETINFO traffic/read
250-traffic/read=
GETINFO traffic/written
250-traffic/written=
GETCONF ControlPort
250 ControlPort=
""".strip().split("\n")

REPLACEMENTS = {
    "SETEVENTS NOTICE ERR NEWDESC NEWCONSENSUS WARN CIRC BW NS":
        "SETEVENTS NEWCONSENSUS BW"
}

FILTER = True

class LineProxyEndpointProtocol(basic.LineReceiver):
    peer = None

    def setPeer(self, peer):
        self.peer = peer

    def lineReceived(self, line):
        allow = False
        if FILTER == False:
            print "%s: %r" % (self.factory.label, line)
            self.peer.transport.write(line + self.delimiter)
            return
        if line in REPLACEMENTS:
            print "%s replacing %r with %r" % (self.factory.label, line, REPLACEMENTS[line])
            line = REPLACEMENTS[line]
            allow = True
        elif line in ALLOWED:
            allow = True
        else:
            for prefix in ALLOWED_PREFIXES:
                if line.startswith(prefix):
                    allow = True
                    break
        if allow:
            print "%s allowed: %r" % (self.factory.label, line,)
            self.peer.transport.write(line + self.delimiter)
        else:
            print "%s filtered: %r" % (self.factory.label, line,)
            if self.factory.label == "tor-control-client":
                print "sending 510"
                self.sendLine("510 Command filtered")

    def connectionMade(self):
        if self.factory.peerFactory.protocolInstance is None:
            self.transport.pauseProducing()
        else:
            self.peer.setPeer(self)

            self.transport.registerProducer(self.peer.transport, True)
            self.peer.transport.registerProducer(self.transport, True)

            self.peer.transport.resumeProducing()

    def connectionLost(self, reason):
        print "connectionLost %r" % (reason,)
        self.transport.loseConnection()
        if self.factory.handleLostConnection is not None:
            self.factory.handleLostConnection(reason)
        return reason

class ProxyEndpointProtocolFactory(protocol.Factory):

    protocol = LineProxyEndpointProtocol

    def __init__(self, handleLostConnection, label=None):
        self.peerFactory = None
        self.protocolInstance = None
        self.handleLostConnection = handleLostConnection
        self.label = label

    def setPeerFactory(self, peerFactory):
        self.peerFactory = peerFactory

    def buildProtocol(self, *args, **kw):
        self.protocolInstance = protocol.Factory.buildProtocol(self, *args, **kw)

        if self.peerFactory.protocolInstance is not None:
            self.protocolInstance.setPeer(self.peerFactory.protocolInstance)

        return self.protocolInstance

class EndpointServerProxy(object):
    def __init__(self, client_endpoint, server_endpoint):
        self.client_endpoint = client_endpoint
        self.server_endpoint = server_endpoint

    def start(self):
        self.start_server()

    def start_server(self):
        server_lost_d = defer.Deferred()
        client_lost_d = defer.Deferred()
        self.proxy_conn_d = defer.DeferredList([server_lost_d, client_lost_d])
        def restart(result):
            self.server_d.cancel()
            self.client_d.cancel()
            self.start_server()
        self.proxy_conn_d.addCallback(restart)

        def handle_server_lost_connection(f):
            print "handle_server_lost_connection %r" % (f,)
            server_lost_d.callback(None)
        def handle_client_lost_connection(f):
            print "handle_client_lost_connection %r" % (f,)
            client_lost_d.callback(None)

        server_factory = ProxyEndpointProtocolFactory(handle_server_lost_connection, label="tor-control-client")
        client_factory = ProxyEndpointProtocolFactory(handle_client_lost_connection, label="server")
        server_factory.setPeerFactory(client_factory)
        client_factory.setPeerFactory(server_factory)
        self.server_d = self.server_endpoint.listen(server_factory)
        self.client_d = self.client_endpoint.connect(client_factory)
