VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "centos/7"

  # Define a test box to be scanned during tests
  config.vm.define "test_1" do |test_1|
        test_1.vm.network "private_network", ip: "192.168.50.10"

        test_1.vm.provision "ansible" do |ansible|
            ansible.playbook = "vagrant/setup-test-vms.yml"
        end
    end

    # Define a test box to be scanned during tests
    config.vm.define "test_2" do |test_2|
          test_2.vm.network "private_network", ip: "192.168.50.11"

          test_2.vm.provision "ansible" do |ansible|
              ansible.playbook = "vagrant/setup-test-vms.yml"
          end
      end

      # Define a test box to be scanned during tests
      config.vm.define "test_3" do |test_3|
            test_3.vm.network "private_network", ip: "192.168.50.12"

            test_3.vm.provision "ansible" do |ansible|
                ansible.playbook = "vagrant/setup-test-vms.yml"
            end
        end
end
