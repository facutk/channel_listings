import grequests
from BeautifulSoup import BeautifulSoup
from cgi import parse_qs
from urlparse import urlparse
import json
from itertools import islice

files = {'zipcodes':'zipcodes.json',
         'zip_listing': 'zip_listing.json',
         'ch_listing': 'ch_listing.json',
         'lineups_csv': 'Lineups.csv',
         'lineups_desc_csv': 'LineupsDesc.csv',
         'ch_listing': 'ch_listing.json',
         'channel_csv': 'ChannelListings.csv'}

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
        for z in f_zipcodes.readlines():
            zipcode = json.loads( z )['zipcode']
            zipcodes.append( zipcode )
    return zipcodes

def read_zipcode_info():
    zipcodes = {}
    with open( files['zipcodes'], 'rb' ) as f_zipcodes:
        for z in f_zipcodes.readlines():
            data = json.loads( z )
            zipcode = data['zipcode']
            zipcodes[ zipcode ] = data['info']
    return zipcodes

def read_lineup_info():
    lineups = {} 
    with open( files['zip_listing'], 'rb' ) as f_listing:
        for line in f_listing.readlines():
            data = json.loads( line )
            lineups[ data['zipcode'] ] = data['lineups']
    return lineups

def read_channel_info():
    channels = {} 
    with open( files['ch_listing'], 'rb' ) as f_listing:
        for line in f_listing.readlines():
            data = json.loads( line )
            channels[ data['lineup'] ] = data['channels']
    return channels

def process_zipcodes():
    zipcodes = read_zipcodes()
    print 'Processing ZipCodes'
    total = len( zipcodes )
    current = 0
    for zipcode_block in list(split_every(8, zipcodes )):
        current += len( zipcode_block )
        print 'Zipcodes [ %s ] - %d of %d - %.2f ' %(', '.join(zipcode_block),
                                                     current, total, 
                                                     100*float( current ) / total )+'%'
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
                                                    current, total,
                                                    100*float( current ) / total )+'%'
        f_channel = open( files['ch_listing'], 'ab' )
        channels = scrap_lineups( lineup_block )
        for channel in channels:
            f_channel.write( json.dumps( channel ) + '\n' )
        f_channel.close()

def format_lineup_info():
    print 'Formatting Lineup Info'
    id_desc = {}
    l_csv = open( files['lineups_csv'], 'ab' )
    ld_csv = open( files['lineups_desc_csv'], 'ab' )
    with open( files['zip_listing'], 'rb' ) as f_listing:
        for line in f_listing.readlines():
            data = json.loads( line )
            zipcode = data['zipcode']
            lineups = data['lineups']
            for l in lineups:
                id = l['id']
                desc = l['name']
                id_desc[ id ] = desc
                l_csv.write('"%s", "%s"'%(zipcode,id)+'\n')
    l_csv.close()
    for id in id_desc:
        ld_csv.write( '"%s", "%s"'%(id, id_desc[id])+'\n')
    ld_csv.close()

def format_channel_info():
    print 'Formatting Channel Info'
    c_csv = open( files['channel_csv'], 'ab' )
    with open( files['ch_listing'], 'rb' ) as f_listing:
        for line in f_listing.readlines():
            data = json.loads( line )
            key = data['lineup']
            value = '|'.join( data['channels'] )
            c_csv.write('"%s", "%s"'%(key,value)+'\n')
    c_csv.close()

def format_csv():
    format_lineup_info()
    format_channel_info()

if __name__ == '__main__':
    process_zipcodes()
    process_lineups()
    format_csv()
    print "Done!"
