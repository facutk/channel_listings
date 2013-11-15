#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse

import urllib
import urllib2
import sys
 

# html parser
from BeautifulSoup import BeautifulSoup

from cgi import parse_qs
from urlparse import urlparse

def get_ch_number( href ):
    """docstring for get_ch_number"""
    return parse_qs( urlparse( href ).query )['channel'][0]

def get_lineup( href ):
    """docstring for get_ch_number"""
    return parse_qs( urlparse( href ).query )['lineupId'][0]



def get_cable_info(zipcode,channel_name,html_ch):

    #print '<p> parsing provider data </p>'
    soup_ch= BeautifulSoup(html_ch)

    grid = soup_ch.findAll('div', {'class': 'zc-grid'})

    for grid_info in grid:
        result_ch= grid_info.findAll('table', {'class': 'zc-row '})

        for ch_info in result_ch:
            ch_data = ch_info.findAll('td', {'class': 'zc-st'})


            for ch_item in ch_data:
                ch_spans = ch_item.findAll('span', {'class': 'zc-st-c'})

                for ch_span in ch_spans:
                    ch_link = ch_span.findAll('a', {'class': 'zc-st-a'})

                    """
                    print ch_link
                    """
                    for ch_stuff in ch_link:

                        ch_url = ch_stuff['href']
                        ch_number = get_ch_number( ch_url )
                        ch_name   = ch_stuff.contents[0].strip()
                        ch_full_data = '<p>'+zipcode+','+channel_name+','+ch_number + ',' + ch_name+'</p>'
                        sys.stdout.write(ch_full_data)
                        sys.stdout.flush()




def get_lineups( zipcode ):
    #print 'zipcode: ', zipcode

    baseurl = 'http://tvlistings.zap2it.com'
    url = baseurl + '/tvlistings/ZBChooseProvider.do?method=getProviders'

    # Prepare the data
    values = {'zipcode' : zipcode}
    data = urllib.urlencode(values)
     
    # Send HTTP POST request
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
     
    html = response.read()
     
    # Print the result
    #print html
    lineups = []

    soup = BeautifulSoup(html)
    result = soup.findAll('div', {'class': 'zc-provider-list'})
    for div in result:
        links = div.findAll('a')
        for a in links:
            channel_name = a.contents[0].strip().replace('&amp;','&')
            #print channel_name
            lineups.append( get_lineup( a['href'] ) )
            #href = baseurl + a['href']

            #req_ch= urllib2.Request(href)
            #response_ch= urllib2.urlopen(req_ch)
     
            #print '<p> retrieving provider data </p>'
            #html_ch= response_ch.read()

     
            #html_ch= open('channel.html','rb').read()
            #get_cable_info(zipcode, channel_name,html_ch)
            lineups.sort()
    return lineups

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Get listings from zipcode')

    parser.add_argument('zipcode', metavar='z', type=int, 
                        help='zipcode to grab listings')

    args = parser.parse_args()

    zipcode = args.zipcode

    for lineup in get_lineups( zipcode ):
        print lineup
