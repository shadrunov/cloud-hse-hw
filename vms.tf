data "yandex_compute_image" "container-optimized-image" {
  family = "container-optimized-image"
}

resource "yandex_compute_instance" "nginx" {
  name     = "hw2-nginx"
  hostname = "nginx"
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.container-optimized-image.id
      size     = 30
    }
  }
  network_interface {
    subnet_id  = yandex_vpc_subnet.lan-net.id
    nat        = true
    ip_address = "192.168.1.4"
  }
  resources {
    cores  = 2
    memory = 2
  }
  scheduling_policy {
    preemptible = true
  }
  metadata = {
    docker-compose = file("nginx/docker-compose.yml")
    user-data      = file("cloud-config.yml")
  }
}


resource "yandex_compute_instance" "nat" {
  name     = "hw2-nat"
  hostname = "nat"
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
      image_id = "fd8drj7lsj7btotd7et5" # nat-instance-ubuntu
      size     = 10
    }
  }
  network_interface {
    subnet_id  = yandex_vpc_subnet.lan-net.id
    nat        = true
    ip_address = "192.168.1.3"
  }
  metadata = {
    user-data = file("cloud-config.yml")
  }
}


resource "yandex_compute_instance" "back1" {
  name     = "hw2-back1"
  hostname = "back1"
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.container-optimized-image.id
      size     = 30
    }
  }
  network_interface {
    subnet_id  = yandex_vpc_subnet.lan-net.id
    nat        = false
    ip_address = "192.168.1.5"
  }
  resources {
    cores  = 2
    memory = 2
  }
  scheduling_policy {
    preemptible = true
  }
  metadata = {
    docker-compose = file("back/docker-compose.prod.yml")
    user-data      = file("cloud-config.yml")
  }
}


resource "yandex_compute_instance" "back2" {
  name     = "hw2-back2"
  hostname = "back2"
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.container-optimized-image.id
      size     = 30
    }
  }
  network_interface {
    subnet_id  = yandex_vpc_subnet.lan-net.id
    nat        = false
    ip_address = "192.168.1.6"
  }
  resources {
    cores  = 2
    memory = 2
  }
  scheduling_policy {
    preemptible = true
  }
  metadata = {
    docker-compose = file("back/docker-compose.prod.yml")
    user-data      = file("cloud-config.yml")
  }
}


resource "yandex_compute_instance" "clickhouse" {
  name     = "hw2-clickhouse"
  hostname = "clickhouse"
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.container-optimized-image.id
      size     = 30
    }
  }
  network_interface {
    subnet_id  = yandex_vpc_subnet.lan-net.id
    nat        = false
    ip_address = "192.168.1.7"
  }
  resources {
    cores  = 2
    memory = 2
  }
  scheduling_policy {
    preemptible = true
  }
  metadata = {
    docker-compose = file("clickhouse/docker-compose.yml")
    user-data      = file("cloud-config.yml")
  }
}
