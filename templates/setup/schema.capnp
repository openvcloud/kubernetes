
@0x806e7822d662ad50;

struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # k8s vdc
    vdc @1 :Text;

    # zerotier network ID. **Required**.
    zerotierId @2 :Text;

    # itsyou.online organization. **Required**.
    organization @3 :Text;

    # ZeroTier authentification token. **Required**.
    zerotierToken @4 :Text;

    # Workers machines
    workers @5 :Int64;

    # sizeId of the worker machines
    sizeId @6 :Int64 = 2;

    # disk size of the worker machine (per size)
    dataDiskSize @7 :Int64 = 10;

    # sshkey for deploying the helper node
    sshKey @8 :Text;

    # cluster credentials returned
    credentials @9 :List(Text);
}