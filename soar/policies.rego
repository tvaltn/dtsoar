package access_policies

violation[packet.data] {
	packet := input.packet
    packet.data == 0
}

violation[packet.data] {
	packet := input.packet
 	packet.data < 0
}