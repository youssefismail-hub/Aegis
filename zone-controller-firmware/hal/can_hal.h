#ifndef CAN_HAL_H
#define CAN_HAL_H

#include <stdint.h>
#include <stddef.h>

/*
 * Hardware Abstraction Layer for CAN.
 *
 * This interface is deliberately hardware-agnostic. It will first be
 * backed by Linux SocketCAN (for Software-in-the-Loop testing on a
 * virtual CAN interface, vcan0, with zero physical hardware). Later, an
 * STM32 FDCAN backend will implement this exact same interface for the
 * Nucleo-G431KB. Nothing in the decode/business logic changes when that
 * happens — only the backend file swaps.
 */

typedef struct {
    uint32_t id;        /* 11-bit or 29-bit CAN identifier */
    uint8_t  dlc;        /* data length, 0-8 */
    uint8_t  data[8];
} can_frame_t;

/* Initialize the CAN interface. iface_name is e.g. "vcan0" on Linux,
 * or ignored/NULL on a real MCU backend where the peripheral is fixed. */
int can_hal_init(const char *iface_name);

/* Send a frame. Returns 0 on success, negative on error. */
int can_hal_send(const can_frame_t *frame);

/* Blocking receive with timeout in milliseconds. Returns 0 on success,
 * -1 on timeout, negative on error. */
int can_hal_receive(can_frame_t *frame, int timeout_ms);

/* Close/release the interface. */
void can_hal_close(void);

#endif /* CAN_HAL_H */