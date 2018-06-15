
@0x806e7822d662ad50;

struct Schema {

    # kubernetes vdc. **Required**.
    vdc @0 :Text;

    # zerotier network ID. **Required**.
    zerotierId @1 :Text;

    # itsyou.online organization. **Required**.
    organization @2 :Text;

    # ZeroTier authentification token. **Required**.
    zerotierToken @3 :Text;

    # number of workers machines. **Required**.
    workersCount @4 :Int64;

    # sshkey to access workers from k8s cluster. **Required**.
    sshKey @5 :SshKey;

   	# Description of the kubernates cluster. ** Optional **.
	description @6 :Text;

    # branches of repo's required for the deployment 
    branch @7 :Branch;
    
    # sizeId of the worker machines
    sizeId @8 :Int64 = 6;

    # disk size of the worker machine (per size)
    dataDiskSize @9 :Int64 = 10;

    # cluster credentials returned. **Autofilled**.
    credentials @10 :List(Text);

    struct SshKey {
        name @0 :Text;
        passphrase @1 :Text;
    }

    struct Branch {
        # branch or 0-Templates of openvcloud
        zeroTemplates @0 :Text; 

        # branch of kubernates templates of openvcloud
        kubernetes @1 :Text;

        # branch of ZOS to install on helper machine
        zos @2 :Text;
    }
}