#ifndef PID_DECODE_H
#define PID_DECODE_H

#include <stdint.h>
#include "../hal/can_hal.h"

/* Standard OBD-II Mode 01 PIDs implemented, per SAE J1979. */
#define OBD_PID_COOLANT_TEMP  0x05
#define OBD_PID_RPM           0x0C
#define OBD_PID_SPEED         0x0D
#define OBD_PID_FUEL_LEVEL    0x2F

#define OBD_REQUEST_ID   0x7DF  /* functional broadcast request */
#define OBD_RESPONSE_ID  0x7E8  /* typical ECU response ID */

/* Builds a Mode 01 request frame for the given PID. */
void obd_build_request(can_frame_t *frame_out, uint8_t pid);

/*
 * Decodes a Mode 01 response frame for the given PID.
 * Returns 0 on success and writes the physical value to *value_out.
 * Returns -1 if the frame doesn't match the expected PID/mode, or if
 * the frame fails basic sanity checks (wrong length, wrong mode byte,
 * or an implausible physical value).
 */
int obd_decode_response(const can_frame_t *frame, uint8_t expected_pid, double *value_out);

#endif /* PID_DECODE_H */