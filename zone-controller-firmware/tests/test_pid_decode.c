/*
 * Unit tests for pid_decode.c — no hardware, no CAN interface needed.
 * Asserts against known-good byte -> physical-value conversions.
 */

#include <stdio.h>
#include <math.h>
#include "../src/pid_decode.h"

static int g_failures = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        printf("FAIL: %s\n", msg); \
        g_failures++; \
    } else { \
        printf("PASS: %s\n", msg); \
    } \
} while (0)

static int nearly_equal(double a, double b, double eps)
{
    return fabs(a - b) < eps;
}

int main(void)
{
    can_frame_t f;
    double v;

    /* RPM: A=0x1A, B=0xF8 -> ((26*256)+248)/4 = 6904/4 = 1726.0 */
    f.id = OBD_RESPONSE_ID; f.dlc = 5;
    f.data[0] = 0x03; f.data[1] = 0x41; f.data[2] = OBD_PID_RPM;
    f.data[3] = 0x1A; f.data[4] = 0xF8;
    CHECK(obd_decode_response(&f, OBD_PID_RPM, &v) == 0 && nearly_equal(v, 1726.0, 0.01),
          "RPM decodes 0x1A 0xF8 to 1726 RPM");

    /* Coolant temp: A=0x5A (90) -> 90-40 = 50 C */
    f.dlc = 4;
    f.data[0] = 0x02; f.data[1] = 0x41; f.data[2] = OBD_PID_COOLANT_TEMP;
    f.data[3] = 0x5A;
    CHECK(obd_decode_response(&f, OBD_PID_COOLANT_TEMP, &v) == 0 && nearly_equal(v, 50.0, 0.01),
          "Coolant temp decodes 0x5A to 50 C");

    /* Speed: A=0x64 (100) -> 100 km/h */
    f.data[0] = 0x02; f.data[1] = 0x41; f.data[2] = OBD_PID_SPEED;
    f.data[3] = 0x64;
    CHECK(obd_decode_response(&f, OBD_PID_SPEED, &v) == 0 && nearly_equal(v, 100.0, 0.01),
          "Speed decodes 0x64 to 100 km/h");

    /* Fuel level: A=0xFF (255) -> 100% */
    f.data[0] = 0x02; f.data[1] = 0x41; f.data[2] = OBD_PID_FUEL_LEVEL;
    f.data[3] = 0xFF;
    CHECK(obd_decode_response(&f, OBD_PID_FUEL_LEVEL, &v) == 0 && nearly_equal(v, 100.0, 0.01),
          "Fuel level decodes 0xFF to 100 percent");

    /* Range check: RPM value that's implausibly high must be rejected. */
    f.data[0] = 0x03; f.data[1] = 0x41; f.data[2] = OBD_PID_RPM;
    f.data[3] = 0xFF; f.data[4] = 0xFF; /* would decode to 16383.75 RPM, way out of range */
    CHECK(obd_decode_response(&f, OBD_PID_RPM, &v) == -1,
          "RPM decode rejects an implausible out-of-range value");

    /* Wrong PID in response must be rejected, not silently misread. */
    f.dlc = 4;
    f.data[0] = 0x02; f.data[1] = 0x41; f.data[2] = OBD_PID_SPEED; /* says speed... */
    f.data[3] = 0x64;
    CHECK(obd_decode_response(&f, OBD_PID_COOLANT_TEMP, &v) == -1,
          "Decode rejects a frame whose PID doesn't match what was requested");

    printf("\n%d failure(s)\n", g_failures);
    return g_failures == 0 ? 0 : 1;
}