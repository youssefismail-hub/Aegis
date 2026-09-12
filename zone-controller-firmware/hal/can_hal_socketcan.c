/*
 * Linux SocketCAN backend for can_hal.h.
 *
 * This lets you build and run the zone controller's CAN decode logic on
 * a laptop against a virtual CAN interface (vcan0), with no physical
 * hardware. Set it up with:
 *
 *   sudo modprobe vcan
 *   sudo ip link add dev vcan0 type vcan
 *   sudo ip link set up vcan0
 */

#include "can_hal.h"

#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/time.h>
#include <linux/can.h>
#include <linux/can/raw.h>

static int s_sock = -1;

int can_hal_init(const char *iface_name)
{
    struct sockaddr_can addr;
    struct ifreq ifr;

    if (!iface_name) {
        fprintf(stderr, "can_hal_init: iface_name required for SocketCAN backend\n");
        return -1;
    }

    s_sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (s_sock < 0) {
        perror("can_hal_init: socket");
        return -1;
    }

    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, iface_name, IFNAMSIZ - 1);
    if (ioctl(s_sock, SIOCGIFINDEX, &ifr) < 0) {
        perror("can_hal_init: ioctl SIOCGIFINDEX (does the interface exist?)");
        close(s_sock);
        s_sock = -1;
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (bind(s_sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("can_hal_init: bind");
        close(s_sock);
        s_sock = -1;
        return -1;
    }

    return 0;
}
int can_hal_send(const can_frame_t *frame)
{
    struct can_frame raw_frame;

    if (s_sock < 0 || !frame) return -1;

    memset(&raw_frame, 0, sizeof(raw_frame));
    raw_frame.can_id = frame->id;
    raw_frame.can_dlc = frame->dlc > 8 ? 8 : frame->dlc;
    memcpy(raw_frame.data, frame->data, raw_frame.can_dlc);

    ssize_t n = write(s_sock, &raw_frame, sizeof(raw_frame));
    if (n != (ssize_t)sizeof(raw_frame)) {
        perror("can_hal_send: write");
        return -1;
    }
    return 0;
}
int can_hal_receive(can_frame_t *frame, int timeout_ms)
{
    struct can_frame raw_frame;
    struct timeval tv;
    fd_set rdfs;

    if (s_sock < 0 || !frame) return -1;

    FD_ZERO(&rdfs);
    FD_SET(s_sock, &rdfs);
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;

    int ret = select(s_sock + 1, &rdfs, NULL, NULL, &tv);
    if (ret == 0) {
        return -1; /* timeout */
    } else if (ret < 0) {
        perror("can_hal_receive: select");
        return -2;
    }

    ssize_t n = read(s_sock, &raw_frame, sizeof(raw_frame));
    if (n != (ssize_t)sizeof(raw_frame)) {
        perror("can_hal_receive: read");
        return -2;
    }

    frame->id = raw_frame.can_id & CAN_EFF_MASK;
    frame->dlc = raw_frame.can_dlc;
    memcpy(frame->data, raw_frame.data, raw_frame.can_dlc);
    return 0;
}

void can_hal_close(void)
{
    if (s_sock >= 0) {
        close(s_sock);
        s_sock = -1;
    }
}