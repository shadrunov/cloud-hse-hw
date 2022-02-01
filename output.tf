output "internal_ip_address_nginx" {
  value = yandex_compute_instance.nginx.network_interface.0.ip_address
}

output "internal_ip_address_nat" {
  value = yandex_compute_instance.nat.network_interface.0.ip_address
}

output "internal_ip_address_back1" {
  value = yandex_compute_instance.back1.network_interface.0.ip_address
}

output "internal_ip_address_back2" {
  value = yandex_compute_instance.back2.network_interface.0.ip_address
}

output "internal_ip_address_clickhouse" {
  value = yandex_compute_instance.clickhouse.network_interface.0.ip_address
}

output "external_ip_address_nat" {
  value = yandex_compute_instance.nat.network_interface.0.nat_ip_address
}

output "external_ip_address_nginx" {
  value = yandex_compute_instance.nginx.network_interface.0.nat_ip_address
}

