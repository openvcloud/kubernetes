
struct Schema {
   	# Description of the cloudspace.
	description @0 :Text;

    # Masters machines
    masters @1 :List(Text);

    # Workers machines
    workers @2 :List(Text);
}