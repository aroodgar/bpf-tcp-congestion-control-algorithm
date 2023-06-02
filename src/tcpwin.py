from bcc import BPF

bpf_text = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <linux/tcp.h>
#include <bcc/proto.h>
#include <linux/sched.h>

// define output data structure in C
struct data_t {
    void *socket;
    unsigned int elapsed;
    int snd_cwnd;
    int snd_ssthresh;
    int sk_sndbuf;
    int sk_wmem_queued;
};
BPF_PERF_OUTPUT(events);

int kprobe__tcp_rcv_established(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb)
{

    struct data_t data = {};

    struct sock *socket = (struct sock*)sk;
    struct tcp_sock *tcps = (struct tcp_sock*)sk;

    unsigned int elapsed = bpf_ktime_get_ns();
    data.socket = sk;
    data.elapsed = elapsed / 1000;
    data.snd_cwnd = tcps->snd_cwnd;
    data.snd_ssthresh = tcps->snd_ssthresh;
    data.sk_sndbuf = socket->sk_sndbuf;
    data.sk_wmem_queued = socket->sk_wmem_queued;

    events.perf_submit(ctx, &data, sizeof(data));
    
    return 0;
}


"""


bpf = BPF(text=bpf_text)

print("event,sock,time_us,snd_cwnd,snd_ssthresh,sk_sndbuf,sk_wmem_queued")

def print_event(cpu, data, size):
    event = bpf["events"].event(data)

    sock = event.socket
    time_us = event.elapsed
    snd_cwnd = event.snd_cwnd
    snd_ssthresh = event.snd_ssthresh
    sk_sndbuf = event.sk_sndbuf
    sk_wmem_queued = event.sk_wmem_queued

    print(f"rcv,{hex(sock)},{time_us},{snd_cwnd},{snd_ssthresh},{sk_sndbuf},{sk_wmem_queued}")



bpf["events"].open_perf_buffer(print_event)
while 1:
    try:
        bpf.perf_buffer_poll()
    except KeyboardInterrupt:
        exit()
