#!/usr/bin/python

import sgmllib, re
from twisted.web import proxy, http
import sys
from twisted.python import log
import json
import cgi
import urllib
import urllib2
from twisted.internet import reactor
from multiprocessing import Process
import time


PROXY_PORT = 8080
WHITELIST = []
STRENGTH = 2
TIME = 600
APPID = "GP5xGLfV34GJfVvtGF974cb1MD2npHKlQS3TLvBekr3o9amI8625.5ClcCtlhnkIk7xEtA--"

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
    request = urllib2.Request (
        url = 'http://boss.yahooapis.com/ysearch/web/v1/' +
              term + '?format=json&view=keyterms'+
              '&appid=' + APPID
        )
    
    httpresp = urllib2.urlopen (request)
    return_values = httpresp.read ()
    httpresp.close()

    wset = []

    for x in json.loads(return_values)['ysearchresponse']['resultset_web']:
        try:
            wset.extend(x['keyterms']['terms'][:3])
        except KeyError:
            pass

    return wset



form = cgi.FieldStorage()
term = form.getvalue('words')

wset = getKeywords(term)

WHITELIST = [re.compile('(?i)'+w.lower()) for w in wset]

prox = WhiteWordProxyFactory();
reactor.listenTCP(PROXY_PORT, prox)
p = Process(target=reactor.run)
p.start()
time.sleep(TIME)
p.terminate()
    
