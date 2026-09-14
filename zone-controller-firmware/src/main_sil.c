/*
 * Software-in-the-Loop test harness.
 *
 * Requests a handful of standard PIDs over a virtual CAN interface
 * (vcan0) and prints decoded values. This is the same can_task logic
 * that will eventually run on the STM32G431KB's FDCAN peripheral —
 * only the HAL backend changes when that day comes.
 *
 * Setup (one time):
 *   sudo modprobe vcan
 *   sudo ip link add dev vcan0 type vcan
 *   sudo ip link set up vcan0
 *
 * In one terminal, run this program. In another, simulate an ECU:
 *   candump vcan0                      # watch requests go out
 *   cansend vcan0 7E8#03410C1AF80000    # fake RPM response (1726 RPM)
 */

#include <stdio.h>
#include <unistd.h>
#include "../hal/can_hal.h"
#include "pid_decode.h"

static void request_and_print(const char *label, uint8_t pid)
{
    can_frame_t req, resp;
    double value;

    obd_build_request(&req, pid);
    if (can_hal_send(&req) != 0) {
        fprintf(stderr, "Failed to send request for %s\n", label);
        return;
    }
    printf("Sent request for %-14s (PID 0x%02X)\n", label, pid);

    if (can_hal_receive(&resp, 2000) != 0) {
        printf("  -> no response within timeout\n");
        return;
    }

    if (obd_decode_response(&resp, pid, &value) == 0) {
        printf("  -> %s = %.2f\n", label, value);
    } else {
        printf("  -> received a frame but couldn't decode it as PID 0x%02X\n", pid);
    }
}

int main(void)
{
    if (can_hal_init("vcan0") != 0) {
        fprintf(stderr, "Could not open vcan0 — run the setup commands in the header comment.\n");
        return 1;
    }

    request_and_print("RPM", OBD_PID_RPM);
    request_and_print("Speed", OBD_PID_SPEED);
    request_and_print("Coolant Temp", OBD_PID_COOLANT_TEMP);
    request_and_print("Fuel Level", OBD_PID_FUEL_LEVEL);

    can_hal_close();
    return 0;
}