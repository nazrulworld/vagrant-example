# -*- coding: utf-8 -*-

import os
import sys
import logging
import platform
import subprocess

__author__ = 'Md Nazrul Islam<connect2nazrul@gmail.com>'


class bcolors(object):

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    @staticmethod
    def disable():
        bcolors.HEADER = ''
        bcolors.OKBLUE = ''
        bcolors.OKGREEN = ''
        bcolors.WARNING = ''
        bcolors.FAIL = ''
        bcolors.ENDC = ''

SUPPORTED_PLATFORMS = {
    "Ubuntu": [
        "trusty",
    ],
}

APT_DEPENDENCIES = {
    "trusty": [
        "zlib1g-dev",
        "libreadline-dev",
        "libxml2-dev",
        "libxslt1-dev",
        "curl",
        "libcurl4-openssl-dev",
        "libffi-dev",
        "git-core",
        "libssl-dev",
        "libreadline-dev",
        "libyaml-dev",
        "libsqlite3-dev",
        "sqlite3",
        "memcached",
        "rabbitmq-server",
        "redis-server",
        "libmemcached-dev",
        "postgresql",
        "postgresql-contrib-9.3",
        "postgresql-client",
        "libpq-dev",
        "nodejs",
        "python-virtualenv",
        "python-pip",
        "supervisor",
        "git",
        "npm",
        "node-jquery",
        "yui-compressor"
    ]
}

# TODO: backport node-{cssstyle,htmlparser2,nwmatcher} to trusty,
# so we can eliminate npm (above) and this section.
NPM_DEPENDENCIES = {
    "trusty": [
        "cssstyle",
        "htmlparser2",
        "nwmatcher",
    ]
}

ENV_PATH = "/srv/CentimaniShoppingMall/env"
CENTIMANI_PATH = "/srv/CentimaniShoppingMall"
PIP_PATH = os.path.join(ENV_PATH, 'bin', 'pip')
PYTHON_PATH = os.path.join(ENV_PATH, 'bin', 'python')
DEVELOPMENT_EGGS_PATH = os.path.join(CENTIMANI_PATH, 'centimani-lib')

DEVELOPMENT_EGGS = [
    os.path.join(DEVELOPMENT_EGGS_PATH, 'centimani.configuration'),
    os.path.join(DEVELOPMENT_EGGS_PATH, 'centimani.override'),
    os.path.join(DEVELOPMENT_EGGS_PATH, 'centimani.security'),
    os.path.join(DEVELOPMENT_EGGS_PATH, 'centimani.user'),
    os.path.join(DEVELOPMENT_EGGS_PATH, 'centimani.rfc6749'),
]

# TODO: Parse arguments properly
if "--travis" in sys.argv:
    CENTIMANI_PATH = "."

LOUD = dict(stdout=sys.stdout, stderr=sys.stderr)


def main():
    log = logging.getLogger("centimani-provisioner")
    # TODO: support other architectures
    if platform.architecture()[0] == '64bit':
        arch = 'amd64'
    else:
        log.critical("Only amd64 is supported.")

    vendor, version, codename = platform.dist()

    if not (vendor in SUPPORTED_PLATFORMS and codename in SUPPORTED_PLATFORMS[vendor]):
        log.critical("Unsupported platform: {} {}".format(vendor, codename))

    subprocess.call(['sudo', 'apt-get', 'update'], **LOUD)
    subprocess.call(['sudo', 'apt-get', 'install', '-y'] + APT_DEPENDENCIES["trusty"], **LOUD)

    if os.path.exists(ENV_PATH) and not os.path.exists(os.path.join(ENV_PATH, 'bin')):
        subprocess.call(['sudo', 'rm', '-rf', ENV_PATH], **LOUD)

    if not os.path.exists(ENV_PATH):
        subprocess.call(['sudo', 'mkdir', '-p', ENV_PATH], **LOUD)
        subprocess.call(['sudo', 'chown', "{}:{}".format(os.getuid(), os.getgid()), ENV_PATH], **LOUD)

    log.debug("Create environment at the location of %s" % ENV_PATH)

    if os.path.exists(os.path.join(ENV_PATH, 'bin', 'python')):
        subprocess.call(['virtualenv', ENV_PATH], **LOUD)

    # Put Python virtualenv activation in our .bash_profile.
    with open(os.path.expanduser('~/.bash_profile'), 'w+') as bash_profile:
        bash_profile.writelines([
            "source .bashrc\n",
            "source %s\n" % (os.path.join(ENV_PATH, "bin", "activate"),),
        ])

    # Switch current Python context to the virtualenv.
    activate_this = os.path.join(ENV_PATH, "bin", "activate_this.py")
    execfile(activate_this, dict(__file__=activate_this))

    log.debug("Start installing python packages.")
    subprocess.call(['pip', 'install', '-r', os.path.join(CENTIMANI_PATH, "requirements.txt")], **LOUD)

    # Install Development Eggs
    for egg in DEVELOPMENT_EGGS:
        print PIP_PATH
        print egg
        subprocess.call(["pip", "install", "-e", egg], **LOUD)

    # Add additional node packages for test-js-with-node.
    subprocess.call(['sudo', 'npm', 'install', '-g'] + NPM_DEPENDENCIES['trusty'], **LOUD)

    # Management commands expect to be run from the root of the project.
    os.chdir(CENTIMANI_PATH)

    if "--travis" in sys.argv:
        os.system("sudo service rabbitmq-server restart")
        os.system("sudo service redis-server restart")
        os.system("sudo service memcached restart")
    #sh.configure_rabbitmq(**LOUD)
    #sh.postgres_init_db(**LOUD)
    #sh.do_destroy_rebuild_database(**LOUD)
    #sh.postgres_init_test_db(**LOUD)
    #sh.do_destroy_rebuild_test_database(**LOUD)

if __name__ == "__main__":
    sys.exit(main())