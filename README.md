# bpf-tcp-congestion-control-algorithm
This repository is intended to be a simple guide for utilizing the eBPF tool in order to write and load a custom TCP congestion control algorithm into the Linux kernel.

# Directory structure
The 'src' directory contains all the codes and scripts needed to follow the guide in the corresponding README.md file.
The 'faq' directory contains possible problems and issues  along with their possible solutions one might encounter while trying to write or load a custom TCP congestion control algorithm into the kernel using eBPF.

# Requirements
- bpftool
> This should be already installed on your linux machine.
- clang-13
> Instructions to install clang-13: https://ubuntu.pkgs.org/20.04/ubuntu-proposed-universe-amd64/clang-13_13.0.1-2ubuntu2~20.04.1_amd64.deb.html
- BPF headers
> Bpf headers don’t come with the kernel distro headers. Run ```sudo apt install libbpf-dev``` to install them.

# Important Note
> This work has been done and tested on kernel version ```5.15```.
