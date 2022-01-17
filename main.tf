terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "0.61.0"
    }
  }
}

provider "yandex" {
  token     = file("token")
  cloud_id  = "b1gf8s7u6aiofbs8ru2a"
  folder_id = "b1glopk0ffss77ku36od"
  zone      = "ru-central1-b"
}




resource "yandex_compute_instance" "vm1" {
  name = "hw1-tf-vm1"

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 100
  }

  scheduling_policy {
    preemptible = true
  }

  boot_disk {
    initialize_params {
      image_id = "fd8pmeqbgiuo4oer7rdj" # debian 11
      size = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet-1.id
    nat       = true
  }

  metadata = {
    user-data = "${file("cloud-config.yml")}"
  }

}


resource "yandex_vpc_network" "network-1" {
  name = "network1"
}

resource "yandex_vpc_subnet" "subnet-1" {
  name           = "subnet1"
  zone           = "ru-central1-b"
  network_id     = yandex_vpc_network.network-1.id
  v4_cidr_blocks = ["192.168.11.0/24"]
}

output "internal_ip_address_vm_1" {
  value = yandex_compute_instance.vm1.network_interface.0.ip_address
}

output "external_ip_address_vm_1" {
  value = yandex_compute_instance.vm1.network_interface.0.nat_ip_address
}
