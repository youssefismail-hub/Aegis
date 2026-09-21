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
void obd_build_dtc_request(can_frame_t *frame_out)
{
    memset(frame_out, 0, sizeof(*frame_out));
    frame_out->id  = OBD_REQUEST_ID;
    frame_out->dlc = 8;
    frame_out->data[0] = 0x01; /* one data byte follows */
    frame_out->data[1] = OBD_MODE_REQUEST_DTC;
    /* No PID for Mode 03 — it requests all stored DTCs at once. */
}

static void decode_single_dtc(uint8_t a, uint8_t b, dtc_code_t *out)
{
    static const char category_letters[4] = {'P', 'C', 'B', 'U'};
    static const char hex_chars[] = "0123456789ABCDEF";

    uint8_t category = (a & 0xC0) >> 6; /* top 2 bits: P/C/B/U */
    uint8_t digit1    = (a & 0x30) >> 4; /* next 2 bits: 0-3 */
    uint8_t digit2    = a & 0x0F;        /* bottom 4 bits: hex digit */
    uint8_t digit3    = (b & 0xF0) >> 4; /* top 4 bits of byte B */
    uint8_t digit4    = b & 0x0F;        /* bottom 4 bits of byte B */

    out->code[0] = category_letters[category];
    out->code[1] = (char)('0' + digit1); /* digit1 is always 0-3, safe as decimal */
    out->code[2] = hex_chars[digit2];
    out->code[3] = hex_chars[digit3];
    out->code[4] = hex_chars[digit4];
    out->code[5] = '\0';
}

int obd_decode_dtc_response(const can_frame_t *frame, dtc_code_t *dtcs_out, int max_dtcs)
{
    if (!frame || !dtcs_out || max_dtcs <= 0) return -1;
    if (frame->dlc < 2) return -1;
    if (frame->data[1] != OBD_MODE_RESPONSE_DTC) return -1; /* not a positive Mode 03 response */

    int count = 0;
    /* DTCs start at byte index 2, two bytes each. */
    for (int i = 2; i + 1 < frame->dlc && count < max_dtcs; i += 2) {
        uint8_t a = frame->data[i];
        uint8_t b = frame->data[i + 1];

        if (a == 0x00 && b == 0x00) {
            break; /* 0x0000 is padding, not a real DTC — stop here */
        }

        decode_single_dtc(a, b, &dtcs_out[count]);
        count++;
    }

    return count;
}