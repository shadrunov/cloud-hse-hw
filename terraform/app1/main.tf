locals {
  registry_name = "todo-registry"
}

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

