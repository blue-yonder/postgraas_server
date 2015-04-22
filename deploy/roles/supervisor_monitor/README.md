This repository is an [ansible](http://ansibleworks.com) role for runnig a service managed by the supervisor daemon.

It is necessary that your supervisord.conf contains a include section such as:
    [include]
    files = conf.d/*.ini
    
The role adds config files to the sm_supervisor_config_dir, that are when included by the supervisord.conf
There is a preconfigured config file in the role's template dir named app.ini.j2, but you can add any config file.

## Installation:
Just put this in your "<ansible_playbook>/requirements.yml" file:

    - src: git+http://trondheim.phi-tps.local/git/ansible_role_supervisor_monitor
      version: v0.1

And check out the repository with ansible-galaxy:

    ansible-galaxy install -r <ansible_playbook>/requirements.yml -p <ansible_playbook>/common_roles

## Usage:

    roles:
      - role: ansible_role_supervisor_monitor
        sm_supervisor_config_dir: /etc/supervisor/conf.d
        sm_supervisor_config: /etc/supervisor/supervisord.conf
        sm_supervisorctl_path: /bin/supervisorctl
        sm_app_name: myapp
        sm_app_home: /home/user/myapp_dir
        sm_command: /home/user/myapp_dir/venv/bin/myapp schedule

This would start a supervisor job named myapp, with a simple config.
Check with:

    /bin/supervisorctl status
