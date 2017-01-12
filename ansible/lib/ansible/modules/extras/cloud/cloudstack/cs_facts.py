#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_facts
short_description: Gather facts on instances of Apache CloudStack based clouds.
description:
     - This module fetches data from the metadata API in CloudStack. The module must be called from within the instance itself.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  filter:
    description:
      - Filter for a specific fact.
    required: false
    default: null
    choices:
      - cloudstack_service_offering
      - cloudstack_availability_zone
      - cloudstack_public_hostname
      - cloudstack_public_ipv4
      - cloudstack_local_hostname
      - cloudstack_local_ipv4
      - cloudstack_instance_id
      - cloudstack_user_data
requirements: [ 'yaml' ]
'''

EXAMPLES = '''
# Gather all facts on instances
- name: Gather cloudstack facts
  cs_facts:

# Gather specific fact on instances
- name: Gather cloudstack facts
  cs_facts: filter=cloudstack_instance_id
'''

RETURN = '''
---
cloudstack_availability_zone:
  description: zone the instance is deployed in.
  returned: success
  type: string
  sample: ch-gva-2
cloudstack_instance_id:
  description: UUID of the instance.
  returned: success
  type: string
  sample: ab4e80b0-3e7e-4936-bdc5-e334ba5b0139
cloudstack_local_hostname:
  description: local hostname of the instance.
  returned: success
  type: string
  sample: VM-ab4e80b0-3e7e-4936-bdc5-e334ba5b0139
cloudstack_local_ipv4:
  description: local IPv4 of the instance.
  returned: success
  type: string
  sample: 185.19.28.35
cloudstack_public_hostname:
  description: public IPv4 of the router. Same as C(cloudstack_public_ipv4).
  returned: success
  type: string
  sample: VM-ab4e80b0-3e7e-4936-bdc5-e334ba5b0139
cloudstack_public_ipv4:
  description: public IPv4 of the router.
  returned: success
  type: string
  sample: 185.19.28.35
cloudstack_service_offering:
  description: service offering of the instance.
  returned: success
  type: string
  sample: Micro 512mb 1cpu
cloudstack_user_data:
  description: data of the instance provided by users.
  returned: success
  type: dict
  sample: { "bla": "foo" }
'''

import os

try:
    import yaml
    has_lib_yaml = True
except ImportError:
    has_lib_yaml = False

CS_METADATA_BASE_URL = "http://%s/latest/meta-data"
CS_USERDATA_BASE_URL = "http://%s/latest/user-data"

class CloudStackFacts(object):

    def __init__(self):
        self.facts = ansible_facts(module)
        self.api_ip = None
        self.fact_paths = {
            'cloudstack_service_offering':  'service-offering',
            'cloudstack_availability_zone': 'availability-zone',
            'cloudstack_public_hostname':   'public-hostname',
            'cloudstack_public_ipv4':       'public-ipv4',
            'cloudstack_local_hostname':    'local-hostname',
            'cloudstack_local_ipv4':        'local-ipv4',
            'cloudstack_instance_id':       'instance-id'
        }

    def run(self):
        result = {}
        filter = module.params.get('filter')
        if not filter:
            for key,path in self.fact_paths.items():
                result[key] = self._fetch(CS_METADATA_BASE_URL + "/" + path)
            result['cloudstack_user_data'] = self._get_user_data_json()
        else:
            if filter == 'cloudstack_user_data':
                result['cloudstack_user_data'] = self._get_user_data_json()
            elif filter in self.fact_paths:
                result[filter] = self._fetch(CS_METADATA_BASE_URL + "/" + self.fact_paths[filter])
        return result


    def _get_user_data_json(self):
        try:
            # this data come form users, we try what we can to parse it...
            return yaml.load(self._fetch(CS_USERDATA_BASE_URL))
        except:
            return None


    def _fetch(self, path):
        api_ip = self._get_api_ip()
        if not api_ip:
            return None
        api_url = path % api_ip
        (response, info) = fetch_url(module, api_url, force=True)
        if response:
            data = response.read()
        else:
            data = None
        return data


    def _get_dhcp_lease_file(self):
        """Return the path of the lease file."""
        default_iface = self.facts['default_ipv4']['interface']
        dhcp_lease_file_locations = [
            '/var/lib/dhcp/dhclient.%s.leases' % default_iface, # debian / ubuntu
            '/var/lib/dhclient/dhclient-%s.leases' % default_iface, # centos 6
            '/var/lib/dhclient/dhclient--%s.lease' % default_iface, # centos 7
            '/var/db/dhclient.leases.%s' % default_iface, # openbsd
        ]
        for file_path in dhcp_lease_file_locations:
            if os.path.exists(file_path):
                return file_path
        module.fail_json(msg="Could not find dhclient leases file.")


    def _get_api_ip(self):
        """Return the IP of the DHCP server."""
        if not self.api_ip:
            dhcp_lease_file = self._get_dhcp_lease_file()
            for line in open(dhcp_lease_file):
                if 'dhcp-server-identifier' in line:
                    # get IP of string "option dhcp-server-identifier 185.19.28.176;"
                    line = line.translate(None, ';')
                    self.api_ip = line.split()[2]
                    break
            if not self.api_ip:
                module.fail_json(msg="No dhcp-server-identifier found in leases file.")
        return self.api_ip


def main():
    global module
    module = AnsibleModule(
        argument_spec = dict(
            filter = dict(default=None, choices=[
                'cloudstack_service_offering',
                'cloudstack_availability_zone',
                'cloudstack_public_hostname',
                'cloudstack_public_ipv4',
                'cloudstack_local_hostname',
                'cloudstack_local_ipv4',
                'cloudstack_instance_id',
                'cloudstack_user_data',
            ]),
        ),
        supports_check_mode=False
    )

    if not has_lib_yaml:
        module.fail_json(msg="missing python library: yaml")

    cs_facts = CloudStackFacts().run()
    cs_facts_result = dict(changed=False, ansible_facts=cs_facts)
    module.exit_json(**cs_facts_result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.facts import *
if __name__ == '__main__':
    main()
