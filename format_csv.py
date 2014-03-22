import json

files = {'zip_listing': 'zip_listing.json',
         'lineups_csv': 'Lineups.csv',
         'lineups_desc_csv': 'LineupsDesc.csv',
         'ch_listing': 'ch_listing.json',
         'channel_csv': 'ChannelListings.csv'}

def fix_lineup_info():
    print 'Fixing Lineup Info'
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
    for id in id_desc:
        ld_csv.write( '"%s", "%s"'%(id, id_desc[id])+'\n')
    l_csv.close()
    ld_csv.close()

def fix_channel_info():
    print 'Fixing Channel Info'
    c_csv = open( files['channel_csv'], 'ab' )
    with open( files['ch_listing'], 'rb' ) as f_listing:
        for line in f_listing.readlines():
            data = json.loads( line )
            key = data['lineup']
            value = '|'.join( data['channels'] )
            c_csv.write('"%s", "%s"'%(key,value)+'\n')
    c_csv.close()

fix_lineup_info()
fix_channel_info()
