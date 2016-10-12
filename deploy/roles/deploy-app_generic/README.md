This repository is an [ansible](http://ansibleworks.com) role for deploying a app and installing a supervisor daemon, with a focus on being simple & usable without root.

## Requirements:

    - virtualenv

## Installation:
Just put this in your "<ansible_playbook>/requirements.yml" file:

    - src: git+ssh://git@code.blue-yonder.org:7999/an/deploy-app_generic.git
      version: v0.1

And check out the repository with ansible-galaxy:

    ansible-galaxy install -r <ansible_playbook>/requirements.yml -p <ansible_playbook>/common_roles

## Usage:
    roles:
        - role: deploy-app_generic
          da_app_package: my_app_pkg
          da_pip_index_url: "{{ pip_index_url }}"
          da_app_name: my_app
          da_config_files:
            - templates/my_app.cfg.j2

This would start a supervisor job named my_app, with a simple config.
Check with:

    venv/bin/supervisorctl status
