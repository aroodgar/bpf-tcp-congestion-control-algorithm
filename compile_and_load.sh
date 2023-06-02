#!/bin/bash

# compiling the bpf_cubic.c example file to created file descriptors for the tcp congestion struct_ops
clang-13 -target bpf -I/usr/include/$(uname -m)-linux-gnu -g -O2 -o bpf_cubic.o -c bpf_cubic.c

# loading the created bpf_cubic.o object file into kernel using bpftool
