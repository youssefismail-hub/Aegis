/*
 * Unit tests for secure_boot.c — no hardware needed.
 */

#include <stdio.h>
#include <string.h>
#include "../src/secure_boot.h"

extern int g_failures; /* shared with test_pid_decode.c's main, see note below */

static void check_secure_boot(int cond, const char *msg)
{
    if (!cond) {
        printf("FAIL: %s\n", msg);
        g_failures++;
    } else {
        printf("PASS: %s\n", msg);
    }
}

void run_secure_boot_tests(void)
{
    const uint8_t key[] = "zone-controller-test-key-do-not-use-in-real-deployment";
    const uint8_t firmware_v1[] = "FIRMWARE_IMAGE_V1_CONTENTS_HERE";
    const uint8_t tampered_firmware[] = "FIRMWARE_IMAGE_V1_CONTENTS_HER3"; /* one byte changed */

    uint8_t valid_hmac[HMAC_SHA256_LEN];
    int rc = compute_hmac_sha256(firmware_v1, sizeof(firmware_v1) - 1, key, sizeof(key) - 1, valid_hmac);
    check_secure_boot(rc == 0, "compute_hmac_sha256 succeeds for a normal image");

    int verify_result = secure_boot_verify(firmware_v1, sizeof(firmware_v1) - 1,
                                            valid_hmac, key, sizeof(key) - 1);
    check_secure_boot(verify_result == 1,
                       "secure_boot_verify accepts a correctly-signed image");

    int tampered_result = secure_boot_verify(tampered_firmware, sizeof(tampered_firmware) - 1,
                                              valid_hmac, key, sizeof(key) - 1);
    check_secure_boot(tampered_result == 0,
                       "secure_boot_verify rejects a tampered image (one byte changed)");

    const uint8_t wrong_key[] = "a-completely-different-key-value";
    int wrong_key_result = secure_boot_verify(firmware_v1, sizeof(firmware_v1) - 1,
                                               valid_hmac, wrong_key, sizeof(wrong_key) - 1);
    check_secure_boot(wrong_key_result == 0,
                       "secure_boot_verify rejects when verified with the wrong key");

    uint8_t garbage_hmac[HMAC_SHA256_LEN];
    memset(garbage_hmac, 0xFF, sizeof(garbage_hmac));
    int garbage_result = secure_boot_verify(firmware_v1, sizeof(firmware_v1) - 1,
                                             garbage_hmac, key, sizeof(key) - 1);
    check_secure_boot(garbage_result == 0,
                       "secure_boot_verify rejects a garbage/missing signature");
}