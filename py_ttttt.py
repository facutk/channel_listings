import grequests
from BeautifulSoup import BeautifulSoup
from cgi import parse_qs
from urlparse import urlparse
import json
import os
from itertools import islice

zipcodes = ['90210', '10007']

files = {'zipcodes':'mini_zipcodes.txt',
         'zip_listing': 'zip_listing.json',
         'ch_listing': 'ch_listing.json'}

def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))

def parse_lineups_id( html ):
    lineup = None
    search_str = "dfp_lid='"
    begin = html.find( search_str )
    if begin > 0:
        begin += len( search_str )
        end = html.find( "'", begin )
        lineup = html[begin: end]
    return lineup

def parse_ch_number( href ):
    return parse_qs( urlparse( href ).query )['channel'][0]

def parse_cable_info( html_ch ):
    lineup_id = parse_lineups_id( html_ch )
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
                    for ch_stuff in ch_link:
                        ch_url = ch_stuff['href']
                        ch_number = parse_ch_number( ch_url )
                        ch_name   = ch_stuff.contents[0].strip()
                        channels.append( ch_number + "-" + ch_name )
    return {'lineup': lineup_id, 'channels': channels}

def parse_lineup( href ):
    return parse_qs( urlparse( href ).query )['lineupId'][0]

def parse_lineups( html ):
    lineups = []
    soup = BeautifulSoup(html)
    zipcode = soup.find(attrs={"name": "zipcode"})['value']
    result = soup.findAll('div', {'class': 'zc-provider-list'})
    for div in result:
        links = div.findAll('a')
        for a in links:
            channel_name = a.contents[0].strip().replace('&amp;','&')
            channel_id = parse_lineup( a['href'] ) 
            lineups.append( {'name': channel_name, 'id':channel_id} )
    return {'zipcode': zipcode, 'lineups': lineups}

def scrap_zipcodes( zipcodes ):
    url = 'http://tvlistings.zap2it.com/tvlistings/ZBChooseProvider.do?method=getProviders'
    rs = ( grequests.post(url, data={'zipcode':z} ) for z in zipcodes )
    map = grequests.map( rs )
    return [ parse_lineups( item.content ) for item in map if item.status_code == 200 ]

def scrap_lineups( lineups ):
    baseurl = "http://tvlistings.zap2it.com/tvlistings/ZCGrid.do?method=decideFwdForLineup&lineupId="
    rs = ( grequests.get(baseurl + lineup ) for lineup in lineups )
    map = grequests.map( rs )
    return [ parse_cable_info( item.content ) for item in map if item.status_code == 200 ]

def read_downloaded_lineups():
    lineups = [] 
    with open( files['zip_listing'], 'rb' ) as f_listing:
        for line in f_listing.readlines():
            for lineup in json.loads( line )['lineups']:
                lineup_id = lineup['id']
                if lineup_id not in lineups:
                    lineups.append( lineup_id )
    return lineups

def read_zipcodes():
    zipcodes = []
    with open( files['zipcodes'], 'rb' ) as f_zipcodes:
        for zipcode in f_zipcodes.readlines():
            zipcodes.append( zipcode.strip() )
    return zipcodes

def setup():
    try:
        os.remove( files['zip_listing'] )
        os.remove( files['ch_listing'] )
    except OSError:
        pass

def process_zipcodes():
    zipcodes = read_zipcodes()
    print 'Processing ZipCodes'
    total = len( zipcodes )
    current = 0
    for zipcode_block in list(split_every(8, zipcodes )):
        current += len( zipcode_block )
        print 'Zipcodes [ %s ] - %d of %d - %.2f ' %(', '.join(zipcode_block),
                                                     current, 
                                                     total, 
                                                     100*float( current ) / total )+' %'
        f_listing = open( files['zip_listing'], 'ab' )
        zips =  scrap_zipcodes( zipcode_block )
        for zip in zips:
            f_listing.write( json.dumps(zip) + '\n' )
        f_listing.close()

def process_lineups():
    lineups = read_downloaded_lineups()
    print 'Processing Lineups'
    total = len( lineups )
    current = 0
    for lineup_block in list(split_every(4, lineups )):
        current += len( lineup_block )
        print 'Lineups [ %s ] - %d of %d - %.2f ' %(', '.join(lineup_block),
                                                    current,
                                                    total,
                                                    100*float( current ) / total )+' %'
        f_channel = open( files['ch_listing'], 'ab' )
        channels = scrap_lineups( lineup_block )
        for channel in channels:
            f_channel.write( json.dumps( channel ) + '\n' )
        f_channel.close()

#setup()
#process_zipcodes()
#process_lineups()


