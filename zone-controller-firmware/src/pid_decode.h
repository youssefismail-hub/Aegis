#ifndef PID_DECODE_H
#define PID_DECODE_H

/* Mode 03: request stored DTCs. No PID needed — just mode 03 alone. */
#define OBD_MODE_REQUEST_DTC   0x03
#define OBD_MODE_RESPONSE_DTC  0x43  /* 0x40 + mode, per SAE J1979 */

#define OBD_MAX_DTCS_PER_FRAME 3  /* (8-byte frame - 2 header bytes) / 2 bytes per DTC */

/* Standard OBD-II Mode 01 PIDs implemented, per SAE J1979. */
#define OBD_PID_COOLANT_TEMP  0x05
#define OBD_PID_RPM           0x0C
#define OBD_PID_SPEED         0x0D
#define OBD_PID_FUEL_LEVEL    0x2F

#define OBD_REQUEST_ID   0x7DF  /* functional broadcast request */
#define OBD_RESPONSE_ID  0x7E8  /* typical ECU response ID */


#include <stdint.h>
#include "../hal/can_hal.h"



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


/* A decoded DTC as a human-readable 5-character code, e.g. "P0301". */
typedef struct {
    char code[6]; /* 5 chars + null terminator */
} dtc_code_t;

/* Builds a Mode 03 request frame (no PID — requests all stored DTCs). */
void obd_build_dtc_request(can_frame_t *frame_out);

/*
 * Decodes a Mode 03 response frame into 0-3 DTC codes (simplified
 * single-frame assumption — a real ECU with many DTCs would need
 * multi-frame ISO-TP reassembly, out of scope for this stage).
 * Returns the number of DTCs found (0 means no active codes), or -1 on
 * a malformed/unexpected frame.
 */
int obd_decode_dtc_response(const can_frame_t *frame, dtc_code_t *dtcs_out, int max_dtcs);






#endif /* PID_DECODE_H */