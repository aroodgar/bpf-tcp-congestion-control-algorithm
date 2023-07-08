from bcc import BPF

bpf_text = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <linux/tcp.h>
#include <bcc/proto.h>
#include <linux/sched.h>

// define output data structure in C
struct timer_t {
    void *socket;
    unsigned int elapsed;
};

struct data_t {
    // char socket[50];
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
    unsigned int elapsed = bpf_ktime_get_ns();

    struct data_t data = {};

    struct sock *socket = (struct sock*)sk;
    struct tcp_sock *tcps = (struct tcp_sock*)sk;

    // char str_sk[50];
    // sprintf(str_sk, "%llx", sk);
    // strcpy(data.socket, str_sk);
    data.socket = sk;
    data.elapsed = elapsed / 1000;
    data.snd_cwnd = tcps->snd_cwnd;
    data.snd_ssthresh = tcps->snd_ssthresh;
    data.sk_sndbuf = socket->sk_sndbuf;
    data.sk_wmem_queued = socket->sk_wmem_queued;

    events.perf_submit(ctx, &data, sizeof(data));
    
    return 0;
}

BPF_PERF_OUTPUT(timer_events);
int kprobe__tcp_retransmit_timer(struct pt_regs *ctx, struct sock *sk)
{
    unsigned int elapsed = bpf_ktime_get_ns();

    struct timer_t time_data = {};
    struct sock *socket = (struct sock*)sk;

    time_data.socket = sk;
    time_data.elapsed = elapsed / 1000;

    timer_events.perf_submit(ctx, &time_data, sizeof(time_data));

    return 0;
}


BPF_PERF_OUTPUT(retrans_events);
int kprobe____tcp_retransmit_skb(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb, int segs)
{
    unsigned int elapsed = bpf_ktime_get_ns();

    struct timer_t retrans_data = {};
    struct sock *socket = (struct sock*)sk;

    retrans_data.socket = sk;
    retrans_data.elapsed = elapsed / 1000;

    retrans_events.perf_submit(ctx, &retrans_data, sizeof(retrans_data));

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

def print_timer_event(cpu, data, size):
    timer_event = bpf["timer_events"].event(data)

    sock = timer_event.socket
    time_us = timer_event.elapsed

    print(f"timer,{hex(sock)},{time_us}")

def print_retrans_event(cpu, data, size):
    retrans_event = bpf["retrans_events"].event(data)

    sock = retrans_event.socket
    time_us = retrans_event.elapsed

    print(f"retrans,{hex(sock)},{time_us}")




bpf["events"].open_perf_buffer(print_event)
bpf["timer_events"].open_perf_buffer(print_timer_event)
bpf["retrans_events"].open_perf_buffer(print_retrans_event)
while 1:
    try:
        bpf.perf_buffer_poll()
    except KeyboardInterrupt:
        exit()
