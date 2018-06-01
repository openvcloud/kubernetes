
@0xe98c0ff4e7232c00;

struct Schema {
    # VDC name (required)
    vdc @0 :Text;

    # Account name (required)
    account @1 :Text

    # OpnevCloud connection data
    ovcConnect @2: Connection;

   	# Claster description (optional)
	description @3 :Text;

    # Size ID of a master machine
    masterSizeId @4 :Int64 = 2;

    # Size ID of a worker machine
    workerSizeId @5 :Int64 = 2;

    dataDiskSize @6 :Int64 = 10;

    # Number of worker machines
    workersCount @7 :Int64 = 1;

    # sshkey name
    sshKey @8 :Text = "k8s_id";

    # Masters machines (autofilled)
    masters @9 :List(Text);

    # Workers machines (autofilled)
    workers @10 :List(Text);

    # Kubernetes credentials (autofilled)
    credentials @11 :List(Text);

    struct Connection {
        # OVC address (URL) (required)
        address @0 :Text;

        # IYO Token (required)
        token @1 :Text;

        # Location (required)
        location @2 :Text;

        # OpenvCloud port
        port @3 :UInt16 = 443;

        # instance name
        name @4 :Text = "k8sConnection";
    }
}