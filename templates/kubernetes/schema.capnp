
@0xe98c0ff4e7232c00;

struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # Masters machines (autofilled)
    masters @1 :List(Text);

    # Workers machines (autofilled)
    workers @2 :List(Text);

    masterSizeId @3 :Int64 = 2;

    sizeId @4 :Int64 = 2;

    dataDiskSize @5 :Int64 = 10;

    workersCount @6 :Int64 = 1;

    sshKey @7 :Text;

    vdc @8 :Text;

    credentials @9 :List(Text);
}