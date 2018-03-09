
@0xe98c0ff4e7232c00;

struct Schema {
    # k8s vdc
    vdc @0 :Text;

    # Total number of worker machines to be created
    workerCount @1 :Int64 = 1;

    # sizeId of the master machine
    masterSizeId @2 :Int64 = 2;

    # sizeId of the worker machines
    workerSizeId @3 :Int64 = 2;

    # disk size of the worker machine (per size)
    workerDataDiskSize @4 :Int64 = 10;

    # Masters machines, should not be in the blueprint
    masters @5 :List(Text);

    # Workers machines, should not be in the blueprint
    workers @6 :List(Text);

    # connection to k8s, should not be in the blueprint
    connectionInfo @7 :Text;   
}