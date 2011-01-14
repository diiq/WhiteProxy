#!/usr/bin/python

import sgmllib, re
from twisted.web import proxy, http
import sys
from twisted.python import log
import json
import optparse
import urllib
import urllib2
from twisted.internet import reactor
from multiprocessing import Process
import time
from optparse import OptionParser

WHITELIST = []
STRENGTH = 2 # bigger the number, the fewer sites get by.
APPID = "GP5xGLfV34GJfVvtGF974cb1MD2npHKlQS3TLvBekr3o9amI8625.5ClcCtlhnkIk7xEtA--"

parser = OptionParser("./prox.py \"word or phrase\" \n\nActs as a proxy server serving only sites containing the whitelisted phrase (or semantically associated words or phrases).")
parser.add_option("-p", "--port", dest="PROXY_PORT",
                  help="What port to serve", metavar="#", default=8080)
parser.add_option("-t", "--time",
                  help="Duration to serve", dest="TIME", metavar="m", default=10)
(OPTIONS, ARGS) = parser.parse_args()


class WordCheck(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.chardata = []
        self.inBody = False

    def start_body(self, attrs):
        self.inBody = True

    def end_body(self):
        self.inBody = False

    def handle_data(self, data):
        if self.inBody:
            self.chardata.append(data)

    def getWords(self):
        wdat = "".join(self.chardata);
        count = 0
        for looker in WHITELIST:
            if looker.search(wdat):
                count += 1;
                print looker.search(wdat).group()
        print count
        return count >= STRENGTH, wdat
        


class WhiteWordProxyClient(proxy.ProxyClient):
    alldat = ""
    def __init__(self):
        self.enc = False;
        proxy.ProxyClient.__init__(self)

    def handleHeader(self, key, value):
        proxy.ProxyClient.handleHeader(self, key, value)
        if key.lower( ) == "content-type":
            if value.split(';')[0] == 'text/html':
                self.parser = WordCheck()

    def handleResponsePart(self, data):
        if hasattr(self, 'parser'): 
            self.parser.feed(data)
            self.alldat += data
        else:
            proxy.ProxyClient.handleResponsePart(self, data)
           
    def handleResponseEnd(self):
        white = 0
        if hasattr(self, 'parser'):
            self.parser.close( )
            white, dats = self.parser.getWords()
            del(self.parser)

        if not white:
            proxy.ProxyClient.handleResponsePart(
                self, 
                "Nope, not within your current semantic network.")
        else:
            proxy.ProxyClient.handleResponsePart(self, self.alldat)

        proxy.ProxyClient.handleResponseEnd(self)


class WhiteWordProxyClientFactory(proxy.ProxyClientFactory):
    def buildProtocol(self, addr):
        client = proxy.ProxyClientFactory.buildProtocol(self, addr)
        client.__class__ = WhiteWordProxyClient
        return client

class WhiteWordProxyRequest(proxy.ProxyRequest):
    protocols = {'http': WhiteWordProxyClientFactory}

    def process(self):
        try:
            self.received_headers['accept-encoding'] = "identity;";
        except KeyError:
            pass
        proxy.ProxyRequest.process(self)

class WhiteWordProxy(proxy.Proxy):

    def requestFactory(self, *args):
        return WhiteWordProxyRequest(*args)


class WhiteWordProxyFactory(http.HTTPFactory):

    def buildProtocol(self, addr):
        protocol = WhiteWordProxy()
        return protocol


def getKeywords(terms):
    # This calls a yahoo api, that returns search results,
    # and keywords from those pages. 

    request = urllib2.Request (
        url = 'http://boss.yahooapis.com/ysearch/web/v1/' +
              terms + '?format=json&view=keyterms'+
              '&appid=' + APPID
        )
    
    httpresp = urllib2.urlopen (request)
    return_values = httpresp.read ()
    httpresp.close()

    wset = []

    for x in json.loads(return_values)['ysearchresponse']['resultset_web']:
        try:
            wset.extend(x['keyterms']['terms'][:4]) #magic number, tune as desired.
        except KeyError:
            pass

    return wset


# Awww, look at the lazy globals. They're so cute. 
wset = getKeywords(urllib.quote(ARGS[-1]))

WHITELIST = [re.compile('(?i)'+w.lower()) for w in wset]

prox = WhiteWordProxyFactory();
reactor.listenTCP(OPTIONS.PROXY_PORT, prox)
p = Process(target=reactor.run)
p.start()
time.sleep(OPTIONS.TIME*60)
p.terminate()
    
