
@0x806e7822d662ad50;

struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # k8s vdc
    vdc @1 :Text;

    # Workers machines
    workers @2 :Int64;

    # memory size of the worker machine (per machine)
    memory @3 :Int64;

    # disk size of the worker machine (per size)
    diskSize @4 :Int64;

    # sshkey for deploying the helper node
    sshKey @5 :Text;
}