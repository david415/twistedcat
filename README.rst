

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

   
example usage::

   ./bin/nocat  -s tcp:interface=127.0.0.1:8080 -s tcp:interface=127.0.0.1:8081


contact
-------

Bugfixes with pull requests welcome!

  - email dstainton415@gmail.com
  - gpg key ID 0x836501BE9F27A723
  - gpg fingerprint F473 51BD 87AB 7FCF 6F88  80C9 8365 01BE 9F27 A723

