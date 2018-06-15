
@0x995d368f2d81d9b6;

struct Schema {
    # VDC name (required)
    vdc @0 :Text;

    # Account name (required)
    account @1 :Text;

    # OpnevCloud connection data (required)
    connection @2 :Connection;

    # sshkey name (required)
    sshKey @3 :SshKey;

   	# Claster description (optional)
	description @4 :Text;

    # Size ID of a master machine
    masterSizeId @5 :Int64 = 2;

    # Size ID of a worker machine
    workerSizeId @6 :Int64 = 2;

    # Size of data disk in GB
    dataDiskSize @7 :Int64 = 10;

    # Number of worker machines
    workersCount @8 :Int64 = 1;

    # Masters machines (autofilled)
    masters @9 :List(Text);

    # Workers machines (autofilled)
    workers @10 :List(Text);

    # Kubernetes credentials (autofilled)
    credentials @11 :List(Text);

    branch @12 :Branch;

    struct Branch {
        zeroTemplates @0 :Text = "master";
        kubernetes @1 :Text = "master";
    }

    struct Connection {
        # OVC address (URL)
        address @0 :Text;

        # IYO Token
        token @1 :Text;

        # Location
        location @2 :Text;

        # OpenvCloud port
        port @3 :UInt16;

        # instance name
        name @4 :Text;
    }
    struct SshKey {
        name @0 :Text;
        passphrase @1 :Text;
    }
}