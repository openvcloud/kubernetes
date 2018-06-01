@0xd37ff48ad935931f;
struct Schema {
	# Machine name. **Required**.
	name @0 :Text;

	# Virtual Data Center id. **Required**.
	vdc @1 :Text;

    # zerotier network ID. **Required**.
    zerotierId @2 :Text;

    # itsyou.online organization. **Required**.
    organization @3 :Text;

    # ZeroTier clinet instance name. **Required**.
    zerotierClient @4 :Text;

	# Description for the VM. **Optional**.
	description @5 :Text;

	# OS Image
	osImage @6 :Text = "IPXE Boot";

	# Branch of Zero-os
	branch @7 :Text = "master";

	# Memory available for the vm in GB
	bootDiskSize @8 :Int64 = 10;

	# Type of VM: defines the number of CPU and memory available for the vm
	sizeId @9 :Int64 = 2;

	# Number of CPUs. **Filled in automatically, don't specify it in the blueprint**.
	vCpus @10 :Int64;

	# Memory in MB. **Filled in automatically, don't specify it in the blueprint**.
	memSize @11 :Int64;

	# ID of the VM. **Filled in automatically, don't specify it in the blueprint**
	machineId @12 :Int64 = 0;

	# Public ip of the VM. **Filled in automatically, don't specify it in the blueprint**
	ipPublic @13 :Text;

	# Private ip of the VM. **Filled in automatically, don't specify it in the blueprint**
	ipPrivate @14 :Text;

	# ZeroTier node ID *Filled in automatically, don't specify it in the blueprint**
	zerotierPublicIP @15 :Text;
}