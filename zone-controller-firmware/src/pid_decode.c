#include "pid_decode.h"
#include <string.h>

void obd_build_request(can_frame_t *frame_out, uint8_t pid)
{
    memset(frame_out, 0, sizeof(*frame_out));
    frame_out->id  = OBD_REQUEST_ID;
    frame_out->dlc = 8;
    frame_out->data[0] = 0x02; /* number of additional data bytes */
    frame_out->data[1] = 0x01; /* Mode 01: show current data */
    frame_out->data[2] = pid;
    /* data[3..7] unused, left zero-padded per ISO 15765-4 */
}

int obd_decode_response(const can_frame_t *frame, uint8_t expected_pid, double *value_out)
{
    if (!frame || !value_out) return -1;

    /* Basic sanity checks before trusting anything in the frame. */
    if (frame->dlc < 3) return -1;                 /* too short to be Mode 01 response */
    if (frame->data[1] != 0x41) return -1;          /* 0x41 = positive response to Mode 01 */
    if (frame->data[2] != expected_pid) return -1;  /* not the PID we asked about */

    uint8_t a = frame->data[3];
    uint8_t b = (frame->dlc > 4) ? frame->data[4] : 0;

    switch (expected_pid) {
        case OBD_PID_COOLANT_TEMP:
            *value_out = (double)a - 40.0;
            if (*value_out < -40.0 || *value_out > 215.0) return -1; /* range check */
            return 0;

        case OBD_PID_RPM:
            *value_out = ((double)a * 256.0 + (double)b) / 4.0;
            if (*value_out < 0.0 || *value_out > 8000.0) return -1; /* range check */
            return 0;

        case OBD_PID_SPEED:
            *value_out = (double)a; /* km/h */
            if (*value_out > 300.0) return -1; /* range check */
            return 0;

        case OBD_PID_FUEL_LEVEL:
            *value_out = (double)a * 100.0 / 255.0; /* percent */
            return 0;

        default:
            return -1; /* PID not implemented yet */
    }
}