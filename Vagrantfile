VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "centos/7"

  # Define a test box to be scanned during tests
  config.vm.define "test_1" do |test_1|
        test_1.vm.network "private_network", ip: "192.168.50.10"
        test_1.vm.host_name = "test1.example.com"

        test_1.ssh.forward_x11 = true

        test_1.vm.provision "ansible" do |ansible|
            ansible.playbook = "vagrant/test_rhel.yml"
        end
    end

    # Define a test box to be scanned during tests
    config.vm.define "test_2" do |test_2|
          test_2.vm.network "private_network", ip: "192.168.50.11"
          test_2.vm.host_name = "test2.example.com"

          test_2.ssh.forward_x11 = true

          test_2.vm.provision "ansible" do |ansible|
              ansible.playbook = "vagrant/test_rhel.yml"
          end
      end

      # Define a test box to be scanned during tests
      config.vm.define "test_3" do |test_3|
            test_3.vm.network "private_network", ip: "192.168.50.12"
            test_3.vm.host_name = "test3.example.com"

            test_3.ssh.forward_x11 = true

            test_3.vm.provision "ansible" do |ansible|
                ansible.playbook = "vagrant/test_rhel.yml"
            end
        end
end
