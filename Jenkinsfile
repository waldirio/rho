node('rhel7-os') {
    stage('Setup') {
        sh "whoami"
        withCredentials([file(credentialsId: 'd7ad70b5-0d27-47bb-882b-b50ebe39c5e3', variable: 'RHEL7_REPO')]) {
            sh 'sudo cp ${RHEL7_REPO} /etc/yum.repos.d/rcm-internal.repo'
        }
        sh "sudo cat /etc/yum.repos.d/rcm-internal.repo"
        sh "sudo yum -y groupinstall 'Development Tools'"
        sh "sudo yum -y install python-devel python-crypto rpm-build"
    }
    stage('Install') {
        checkout scm
        createVirtualEnv 'env'
        executeIn 'env', 'python -V'
        executeIn 'env', 'pip install --upgrade setuptools pip'
        executeIn 'env', 'pip install -r requirements.txt'
    }
    stage('Build RPM') {
        executeIn 'env', 'make build-rpm'
        sh "ls -lta ."
        sh "ls -lta dist"
        archive 'dist/*.rpm'
    }
}

def createVirtualEnv(String name) {
    sh "virtualenv --clear ${name}"
    sh "virtualenv ${name}"
}

def executeIn(String environment, String script) {
    sh "source ${environment}/bin/activate && " + script
}
