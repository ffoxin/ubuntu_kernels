#!/usr/bin/env python3


import os
import re
import time

from shutil import move
from sys import stdout
from urllib import request


def shorten_net_speed(speed):
    mod = 1000

    if speed < mod:
        return speed, ''

    speed /= mod
    if speed < mod:
        return speed, 'K'

    speed /= mod
    if speed < mod:
        return speed, 'M'

    speed /= mod
    return speed, 'G'


def print_status(name, done_size, total_size, start_time):
    full_len = 80
    name_len = len(name)
    if name_len < full_len:
        name += '.' * (full_len - len(name))
    elif name_len > full_len:
        name = name[:full_len]

    done_len = full_len * done_size // total_size
    now = time.time()

    speed = done_size / (now - start_time)
    stdout.write('\r  [{}{}] {:5.2f} {}b/s   '.format(
        name[:done_len],
        ' ' * (full_len - done_len),
        *shorten_net_speed(speed)
    ))

    if done_size >= total_size:
        stdout.write('\n')


def main():
    branches = [
        'daily/current',
        'v4.4.11-xenial'
    ]

    save_path = 'deb'
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    checksum_file = 'CHECKSUMS'
    for branch in branches:
        main_url = 'http://kernel.ubuntu.com/~kernel-ppa/mainline/{}/'.format(branch)

        checksum_url = main_url + checksum_file
        request.urlretrieve(checksum_url, checksum_file)

        with open(checksum_file) as f:
            checksums = f.read().split('\n')

        file_block = False
        deb_urls = []
        version = None  # kernel version
        for line in checksums:
            if not file_block and 'Checksums-Sha1:' in line:
                file_block = True
            if file_block and 'Checksums-Sha256:' in line:
                break
            if line.startswith('#'):
                continue
            checksum, filename = line.split('  ')

            if filename.endswith('_all.deb') or filename.endswith('_amd64.deb') and 'generic' in filename:
                deb_urls.append((main_url, filename))
                if version is None:
                    groups = re.search(r'\w+-\w+-(\d+\.\d+\.\d+-\d+)[-_].*', filename).groups()
                    if len(groups) == 1:
                        version = groups[0]

        print('{} ({})'.format(branch, version))
        save_dir = os.path.join(save_path, version)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        os.rename(checksum_file, os.path.join(save_dir, checksum_file))
        for url_data in deb_urls:
            url = '{}{}'.format(*url_data)
            path = os.path.join(save_dir, url_data[1])
            if not os.path.exists(path):
                start_time = time.time()
                request.urlretrieve(url, path, lambda blocks, block_size, total_size: print_status(url_data[1], blocks * block_size, total_size, start_time))


if __name__ == '__main__':
    main()
