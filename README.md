# bpf-tcp-congestion-control-algorithm
This repository is intended to be a simple guide for utilizing the eBPF tool in order to write and load a custom TCP congestion control algorithm into the Linux kernel.

# General guide
- Make sure you have all the [requirements](#requirements) installed.
- Follow the steps according the [compile_and_load.sh](src/compile_and_load.sh) file (Run the commands in the **`src`** directory).
- In case of any problems and issues, refer to [this](#common-issues-and-possible-fixes) section.

# Directory structure
The **`src`** directory contains all the codes and scripts needed to follow the guide in the corresponding README.md file.
The **`FAQ`** directory contains possible problems and issues  along with their possible solutions one might encounter while trying to write or load a custom TCP congestion control algorithm into the kernel using eBPF.

# Requirements
- bpftool
> This should be already installed on your linux machine.
- clang-13
> Instructions to install clang-13 on Ubuntu 20.04: 
> 
> https://ubuntu.pkgs.org/20.04/ubuntu-proposed-universe-amd64/clang-13_13.0.1-2ubuntu2~20.04.1_amd64.deb.html
- BPF headers
> Bpf headers don’t come with the kernel distro headers.
> 
> Run `sudo apt install libbpf-dev` to install them.
- bcc
> Github repository link: https://github.com/iovisor/bcc/tree/master
> 
> Installation guide: https://github.com/iovisor/bcc/tree/master

# Important Note
> This work has been done and tested on Ubuntu 20.04 with kernel version `5.15`.

# Common issues and possible fixes
The following problem would most probably occur if you are using a clang version older than clang-13.

## Main Problem 1
You have original bpf_cubic.c (the one in this repository is slightly changed which will be discussed later in this file) and bpf_tcp_helpers.h from kernel examples.
The can be found from the following addresses:
`tools/testing/selftests/bpf/progs/bpf_cubic.c`
`tools/testing/selftests/bpf/bpf_tcp_helpers.h`

The code will be compiled using `clang -target bpf -I/usr/include/$(uname -m)-linux-gnu -g -O2 -o bpf_cubic.o -c bpf_cubic.c`.
Then it will be loaded using  `sudo bpftool struct_ops register bpf_cubic.o`.

The ensuing error will be something like this:
`libbpf: failed to find BTF for extern 'tcp_cong_avoid_ai' [41] section: -2`

This shows that bpftool has a problem with finding the BTF mapping for the extern function types used in bpf_cubic.c.

Below cites a note from the README.rst file in the linux source tree located at `tools/testing/selftests/bpf/README.rst`:

```
Kernel function call test and Clang version
===========================================

Some selftests (e.g. kfunc_call and bpf_tcp_ca) require a LLVM support
to generate extern function in BTF.  It was introduced in `Clang 13`__.

Without it, the error from compiling bpf selftests looks like:

.. code-block:: console

  libbpf: failed to find BTF for extern 'tcp_slow_start' [25] section: -2

__ https://reviews.llvm.org/D93563
```

According to the above statement, you will have to install clang-13 using the instructions link provided in the repo README.md file.

## Main Problem 2
Compiling the original code with clang-13 and then loading solves the previous issue of not finding BTF for extern functions ([Main Problem 1](#main-problem-1)). Although, a new one will most probably emerge when trying to load the object file into the kernel using bpftool.

In the error logs, the output of the `sudo bpftool struct_ops register bpf_cubic.o` command ends as follows:
```
libbpf: -- END LOG --
libbpf: failed to load program 'bpf_cubic_cong_avoid'
libbpf: failed to load object 'bpf_cubic.o'
```

The following lines can also be seen:
```
; x = ((__u32)(((__u32)v[shift] + 10) << b)) >> 6;
202: (18) r1 = 0xffffb5740035c000
204: (0f) r1 += r2
205: (71) r1 = *(u8 *)(r1 +0)
R1 invalid mem access 'inv'
```

By commenting and uncommenting different sections of the code in the `bpf_cubic_cong_avoid` function, the problem seems to be in the `cubic_root` function where the following line is being verified by the bpf verifier:
```
x = ((__u32)(((__u32)v[shift] + 10) << b)) >> 6;
```
This was indicated in the error logs above. 
More trial and error suggests that the problem is with the `shift` variable assignment:
```
shift = (a >> (b * 3));
```
Variable `a` is of type __u64 and `b` and `shift` are of type `__u32`. 
Changing the code like this for casting helps to solve the problem.
```
shift = ((__u32)a >> (b * 3));
```

**The change is not necessary for the code to be compiled, but it seems to cause an error when the code is being verified by the bpf verifier.**
