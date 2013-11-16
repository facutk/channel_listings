#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import urllib2

# html parser
from BeautifulSoup import BeautifulSoup

from cgi import parse_qs
from urlparse import urlparse

def get_ch_number( href ):
    """docstring for get_ch_number"""
    return parse_qs( urlparse( href ).query )['channel'][0]

def get_channels( lineup ):
    baseurl = "http://tvlistings.zap2it.com/tvlistings/ZCGrid.do?method=decideFwdForLineup&lineupId="
    href = baseurl + lineup
    req_ch= urllib2.Request(href)
    response_ch= urllib2.urlopen(req_ch)
    html_ch= response_ch.read()
    #print '<p> parsing provider data </p>'
    soup_ch= BeautifulSoup(html_ch)
    grid = soup_ch.findAll('div', {'class': 'zc-grid'})
    channels = []
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
                        channels.append( ch_number + "-" + ch_name )
    return "|".join( channels )


#lineups = open('lineups.txt',"rb").readlines()

#for lineup in lineups:
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get channels from lineup')

    parser.add_argument('lineup', metavar='l', help='lineup to grab channels')

    args = parser.parse_args()

    lineup = args.lineup

    print get_channels( lineup )
