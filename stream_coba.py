from obspy.clients.seedlink.easyseedlink import create_client


def geofon_handle_data(trace):
    print('Received the following trace:')
    print(trace)
    print()


def iris_handle_data(trace):
    print('Received the following trace:')
    print(trace)
    print()


if __name__ == "__main__":
    client = create_client('geofon.gfz-potsdam.de', on_data=geofon_handle_data)
    client.select_stream('GE', 'SMRI', 'SHZ')
    client.select_stream('GE', 'UGM', 'SHZ')

    #client = create_client('172.19.3.150', on_data=geofon_handle_data)
    #client.select_stream('IA', 'SMRI', 'SHZ')
    #print(client.capabilities)
    #client.select_stream('IA', 'UGM', 'SHZ')
    client.run()

    #clientIris = create_client(
     #   'rtserve.iris.washington.edu', on_data=iris_handle_data)
    #clientIris.select_stream('II', 'KAPI', 'BHZ')
    #clientIris.run()
