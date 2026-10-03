#include "secure_boot.h"

#include <openssl/hmac.h>
#include <string.h>

int compute_hmac_sha256(const uint8_t *data, size_t data_len,
                         const uint8_t *key, size_t key_len,
                         uint8_t out[HMAC_SHA256_LEN])
{
    unsigned int out_len = 0;

    unsigned char *result = HMAC(EVP_sha256(), key, (int)key_len,
                                  data, data_len, out, &out_len);

    if (result == NULL || out_len != HMAC_SHA256_LEN) {
        return -1;
    }
    return 0;
}

/*
 * Constant-time comparison. A naive memcmp() or byte-by-byte loop that
 * returns early on the first mismatch leaks timing information an
 * attacker could use to guess the correct HMAC one byte at a time
 * (a real, documented class of attack). This loop always inspects
 * every byte, accumulating differences with OR instead of branching
 * on them, so the function takes the same time regardless of where
 * (or whether) a mismatch occurs.
 */
static int constant_time_equal(const uint8_t *a, const uint8_t *b, size_t len)
{
    uint8_t diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= a[i] ^ b[i];
    }
    return diff == 0;
}

int secure_boot_verify(const uint8_t *image_data, size_t image_len,
                        const uint8_t *expected_hmac,
                        const uint8_t *key, size_t key_len)
{
    if (!image_data || !expected_hmac || !key) return -1;

    uint8_t computed[HMAC_SHA256_LEN];
    if (compute_hmac_sha256(image_data, image_len, key, key_len, computed) != 0) {
        return -1;
    }

    return constant_time_equal(computed, expected_hmac, HMAC_SHA256_LEN) ? 1 : 0;
}