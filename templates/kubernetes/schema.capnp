
@0xe98c0ff4e7232c00;

struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # k8s vdc
    vdc @1 :Text;

    # Total number of worker machines to be created
    workerCount @2 :Int64;

    # sizeId of the master machine
    masterSizeId @3 :Int64 = 2;

    # sizeId of the worker machines
    workerSizeId @4 :Int64 = 2;

    # disk size of the worker machine (per size)
    workerDataDiskSize @5 :Int64 = 10;

    # Masters machines, should not be in the blueprint
    masters @6 :List(Text);

    # Workers machines, should not be in the blueprint
    workers @7 :List(Text);

    # connection to k8s, should not be in the blueprint
    connectionInfo @8 :Text;   
}