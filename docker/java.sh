UBUNTU_VERSION=xenial
echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu ${UBUNTU_VERSION} main" | tee /etc/apt/sources.list.d/webupd8team-java.list
echo "deb-src http://ppa.launchpad.net/webupd8team/java/ubuntu ${UBUNTU_VERSION} main" | tee -a /etc/apt/sources.list.d/webupd8team-java.list
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886
DEBIAN_FRONTEND="noninteractive" apt-get update
# Accept the Oracle License
echo "oracle-java8-installer  shared/accepted-oracle-license-v1-1 boolean true" > /tmp/oracle-license-debconf
/usr/bin/debconf-set-selections /tmp/oracle-license-debconf
rm /tmp/oracle-license-debconf
# Install Oracle JDK 7
DEBIAN_FRONTEND="noninteractive" apt-get -q -y install oracle-java8-installer oracle-java8-set-default
