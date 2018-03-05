
@0x806e7822d662ad50;

struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # k8s vdc
    vdc @1 :Text;

    # Workers machines
    workers @2 :Int64;

    # sizeId of the worker machines
    sizeId @3 :Int64 = 2;

    # disk size of the worker machine (per size)
    dataDiskSize @4 :Int64 = 10;

    # sshkey for deploying the helper node
    sshKey @5 :Text;
}