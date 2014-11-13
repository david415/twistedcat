

==========
twistedcat
==========



overview
--------

twistedcat/nocat can proxy between any two twisted endpoints be they both
client, both server, or client and server endpoints.



install
-------

you can install twistedcat in your python virtual environment like this::

   $ pip install git+https://github.com/david415/twistedcat.git



usage
-----

commandline usage summary::

   usage: nocat [-h] [-c CLIENT] [-s SERVER]
   twistedcat - proxy between any two Twisted endpoints
   optional arguments:
     -h, --help            show this help message and exit
     -c CLIENT, --client CLIENT
                           Twisted client endpoint descriptor string
     -s SERVER, --server SERVER
                           Twisted server endpoint descriptor string
   
