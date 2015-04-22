This repository is an [ansible](http://ansibleworks.com) role for installing a supervisor daemon, with a focus on being simple & usable without root.

The template for the supervisord.conf contains a include section, so that all files (*.ini) in <sv_virtualenv>/etc/supervisor/conf.d where included. This allows you to add custom configs to your supervisord.conf without touching the main config itself.

## Requirements:

    - virtualenv

## Installation:
Just put this in your "<ansible_playbook>/requirements.yml" file:

    - src: git+http://trondheim.phi-tps.local/git/ansible_role_supervisor_venv
      version: v0.1

And check out the repository with ansible-galaxy:

    ansible-galaxy install -r <ansible_playbook>/requirements.yml -p <ansible_playbook>/common_roles

## Usage:
    roles:
      - role: ansible_role_supervisor_venv
        sv_virtualenv: /home/user/myvenv
        sv_http: true

This will ensure a supervisor daemon is installed and running

To monitor a job just add this line to your playbook:
    
    supervisorctl: name=myapp state=restarted supervisorctl_path="{{ sv_virtualenv }}/bin/supervisorctl"
    
Or use [ansible_role_supervisor_monitor](http://trondheim.phi-tps.local/git/ansible_role_supervisor_monitor) which adds configs such as [program:myapp] to your supervisord.conf to run and monitor your app
