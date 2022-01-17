# hw 1

## the task:

create VM, deploy OpenVPN, automatise with Terraform

## progress:

1. +4 points: applied grant in Yandex Cloud
1. +2 points: created VM manually
1. +2 points: deployed OpenVPN [docker image](https://github.com/dockovpn/docker-openvpn)
1. +2 points: prepared `.tf` scripts that create VM and start OpenVPN server automatically.
    - [`main.tf`](./main.tf) — creates network and VM (2/2/10)  
    - [`cloud-config.yml`](./cloud-config.yml) — installs ssh-key, deploys docker and openvpn, creates `client.ovpn` config
    - [`token`](./token) — YC OAuth token

## pictures

![image](https://user-images.githubusercontent.com/44522467/149803677-20b7d43e-0823-4c4e-9870-def19fcfb65b.png)

![image](https://user-images.githubusercontent.com/44522467/149805862-51448cef-3799-412d-b4a2-f644ca91994a.png)