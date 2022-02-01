resource "yandex_vpc_network" "net" {
  name = "hw2-net"
}

resource "yandex_vpc_route_table" "nat-rt" {
  network_id = yandex_vpc_network.net.id

  static_route {
    destination_prefix = "0.0.0.0/0"
    next_hop_address   = "192.168.1.3"
  }
}

resource "yandex_vpc_subnet" "lan-net" {
  name           = "hw2-lan-net"
  zone           = "ru-central1-b"
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = ["192.168.1.0/24"]
  route_table_id = yandex_vpc_route_table.nat-rt.id
}
