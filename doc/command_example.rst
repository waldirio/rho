^^^^^^^^^^^^^^^^^
Example rho Scan
^^^^^^^^^^^^^^^^^

Following is the results of an example rho scan. This is the example of the
profile called 'big_test' and it's host auth mapping
after the original reset. This is for the scan performed on Wed Aug 10 23:33:17
2016. Below you will find the example contents for:

- Host Auth Mapping
- Inventory
- Scan Profile
- Scan Auths
- Output

Example Host Auth Mapping
""""""""""""""""""""""""""

::

   Wed Aug 10 23:33:17 2016
   -------------------------------
   192.168.124.153
   ----------------------
   seven, root, ********, empty
   eight, t_4, ********, empty


   192.168.124.162
   ----------------------
   two, t_2, ********, empty


   192.168.124.174
   ----------------------
   one, root, ********, empty
   five, root, ********, empty
   seven, root, ********, empty


   192.168.124.15
   ----------------------
   five, root, ********, empty
   seven, root, ********, empty


   192.168.121.007
   ----------------------
   six, vagrant, ********, empty



Example Inventory
""""""""""""""""""

::

   [alpha]
   192.168.124.153 ansible_ssh_host=192.168.124.153
   192.168.124.162 ansible_ssh_host=192.168.124.162
   192.168.124.174 ansible_ssh_host=192.168.124.174
   192.168.124.15 ansible_ssh_host=192.168.124.15
   192.168.121.007 ansible_ssh_host=192.168.121.007

   [five]
   192.168.124.15 ansible_ssh_host=192.168.124.15 ansible_ssh_user=root ansible_ssh_pass=thirdpass ansible_ssh_private_key_file=empty


   [six]
   192.168.121.007 ansible_ssh_host=192.168.121.007 ansible_ssh_user=vagrant ansible_ssh_private_key_file=empty


   [one]
   192.168.124.174 ansible_ssh_host=192.168.124.174 ansible_ssh_user=root ansible_ssh_pass=firstpass ansible_ssh_private_key_file=empty


   [two]
   192.168.124.162 ansible_ssh_host=192.168.124.162 ansible_ssh_user=t_2 ansible_ssh_pass=secondpass1 ansible_ssh_private_key_file=empty


   [seven]
   192.168.124.153 ansible_ssh_host=192.168.124.153 ansible_ssh_user=root ansible_ssh_pass=fourthpass ansible_ssh_private_key_file=empty


Example Scan Profile
"""""""""""""""""""""

``big_test, 192.168.124.[1:40],192.168.121.007,192.168.121.140,192.168.124.153,192.168.124.[150:200], test_first,test_second,test_third,one,two,three,four,five,six,seven,eight``

Example Scan Auths
"""""""""""""""""""""

::

   c54de740-6e03-436f-ab46-901a3a07c271, test_first, root, ********, /home/kbattula/.ssh/id_rsa
   ecdda349-f7f3-432f-ac45-84aff1182f98, test_second, root, ********, /home/kbattula/.ssh/id_rsa
   e2b70d19-6c96-426b-962a-c773c0eb9125, test_third, root, ********, /home/kbattula/.ssh/id_rsa
   d2aa29b5-4f90-4da6-adfc-1163d7007568, one, root, ********, empty
   de7ae67b-8880-4b3a-ab3d-365d58da0d69, two, t_2, ********, empty
   55bc67f3-fc64-427c-8b2f-7aa7ceccf59b, three, blippy, ********, empty
   af05cdce-08f7-4e7f-b375-981ad1935c2e, four, foobar, ********, empty
   dc759edd-e43f-4a62-9459-eda6bc0efff8, five, root, ********, empty
   dc72b6e1-f486-4b15-8e25-8c3b2ab395b8, six, vagrant, ********, empty
   f37ce000-dc2a-4a3d-9988-e21caa8cec2b, seven, root, ********, empty
   b11e014b-da64-4c0d-a45d-c81d12419882, eight, t_4, ********, empty

*Note: The first column is the unique id that rho assigns to every auth.*

Auths Association
""""""""""""""""""
This is the order in which the profile was associated to auths:

``test_first test_second test_third one two three four five six seven eight``


Facts
"""""""
The facts collected were:

- Username_uname.hostname
- Username_uname.os
- Date_date.date
- Cpu_cpu.bogomips
- Cpu_cpu.vendor_id
- RedhatRelease_redhat-release.name
- RedhatPackages_redhat-packages.num_installed_packages

Example Output
""""""""""""""""

::

   cpu.bogomips,cpu.vendor_id,date.date,redhat-packages.num_installed_packages,redhat-release.name,uname.hostname,uname.os
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,324,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,328,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,324,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,324,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,379,centos-release,rho-dev.example.com,Linux
