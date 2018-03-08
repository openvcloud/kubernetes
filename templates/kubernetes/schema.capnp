
@0xe98c0ff4e7232c00;

struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # Masters machines
    masters @1 :List(Text);

    # Workers machines
    workers @2 :List(Text);

    # k8s vdc
    vdc @3 :Text;

    # Workers machines
    workers @4 :Int64;

    # sizeId of the worker machines
    sizeId @5 :Int64 = 2;

    # disk size of the worker machine (per size)
    dataDiskSize @6 :Int64 = 10;

    # sshkey for deploying the helper node
    sshKey @7 :Text = 'id_k8s';

    # connection to k8s
    connectionInfo @8 :Text;   
}