resource "yandex_iam_service_account" "todo_ig_sa" {
  name        = "todo-ig-sa"
  description = "service account to manage IG"
}

resource "yandex_resourcemanager_folder_iam_binding" "folder_editor" {
  folder_id   = "b1glopk0ffss77ku36od"
  role = "editor"
  members = [
    "serviceAccount:${yandex_iam_service_account.todo_ig_sa.id}",
  ]
  sleep_after = 30
}

resource "yandex_iam_service_account" "todo_node_sa" {
  name        = "todo-node-sa"
  description = "service account to manage docker images on nodes"
}

resource "yandex_resourcemanager_folder_iam_binding" "folder_puller" {
  folder_id   = "b1glopk0ffss77ku36od"
  role = "container-registry.images.puller"
  members = [
    "serviceAccount:${yandex_iam_service_account.todo_node_sa.id}",
  ]
}
