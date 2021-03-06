#!/usr/bin/env python
import os
import errno
import platform
import sys
import subprocess

# Figure out what type of package to build based on platform info
#
# TODO: Windows does MSI?

deb = ['debian', 'ubuntu']
rpm = ['redhat', 'fedora', 'suse', 'opensuse', 'centos']

dist = platform.dist()[0].lower()


def pkg_type():
    if dist in deb:
        return "deb"

    if dist in rpm:
        return "rpm"

    return None


def pkg_dir():
    system = platform.system().lower()
    machine = platform.machine().lower()
    addon = ""
    if system == "freebsd":
        system = system + platform.release().lower()[0]
    if system == "linux":
        dist = platform.dist()
        # Lower case everyting (looking at you Ubuntu)
        dist = tuple([x.lower() for x in dist])

        # Treat all redhat 5.* versions the same
        # redhat-5.5 becomes redhat-5
        if (dist[0] == "redhat" or dist[0] == "centos"):
            major = dist[1].split(".")[0]
            distro = dist[0]

            # http://bugs.centos.org/view.php?id=5197
            # CentOS 5.7 identifies as redhat
            if int(major) <= 5 and distro == "redhat":
                f = open('/etc/redhat-release')
                new_dist = f.read().lower().split(" ")[0]
                if new_dist == "centos":
                    distro = "centos"

            dist = (distro, major)

        dist = "%s-%s" % dist[:2]
        return "%s-%s" % (dist, machine)

    return "%s-%s%s" % (system, machine, addon)


def sh(cmd):
    print cmd
    rv = subprocess.call(cmd, shell=True)
    if rv != 0:
        print "Exit Code: %s" % (rv)
        sys.exit(1)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def system_info():
    # gather system, machine, and distro info
    machine = platform.machine()
    system = platform.system().lower()
    return (machine, system, pkg_dir())


# git describe return "0.1-143-ga554734"
# git_describe() returns {'release': '143', 'tag': '0.1', 'hash': 'ga554734'}
def git_describe(is_exact=False, split=True):
    options = "--always"

    if is_exact:
        options = "--exact-match"

    describe = "git describe --tags %s" % (options)

    try:
        p = subprocess.Popen(describe,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True)
    except OSError as e:
        print "ERROR: running: %s" % describe
        print e
        sys.exit(1)

    version, errors = p.communicate()
    if (len(errors)):
        print(errors)
        return None

    version = version.strip()
    if split:
        version = version.split('-')

    return version


def package_builder_dir():
    """returns the directory that is packaged into rpms/debs.
    This is useful because the builders maybe specifiy different cflags, etc, which
    interfere with generating symbols files."""

    pkgType = pkg_type()
    basePath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    buildDirArgs = [basePath, 'out']

    if pkgType == 'deb':
        buildDirArgs += ('debbuild', 'rackspace-monitoring-agent')
    elif pkgType == 'rpm':
        buildDirArgs += ('rpmbuild', 'BUILD', "virgo-%s" % ("-".join(git_describe())))
    else:
        raise AttributeError('Unsupported pkg type, %s' % (pkgType))

    buildDirArgs += ('out', 'Debug')

    return os.path.join(*buildDirArgs)

if __name__ == "__main__":
    print pkg_type()
