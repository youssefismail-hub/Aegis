#ifndef SECURE_BOOT_H
#define SECURE_BOOT_H

#include <stdint.h>
#include <stddef.h>

/*
 * Secure-boot verification simulation. See docs/decisions/0007 for why
 * this uses HMAC-SHA256 via OpenSSL here, instead of the real target
 * (mbedTLS + secure-element-backed ECDSA on actual hardware).
 *
 * The core property being proven: a firmware image whose HMAC doesn't
 * match what the (simulated) secure element expects must be rejected,
 * regardless of how "close" it looks to a valid image.
 */

#define HMAC_SHA256_LEN 32

/*
 * Computes HMAC-SHA256 over `data` using `key`, writing the 32-byte
 * result into `out`. Returns 0 on success, -1 on failure (e.g. OpenSSL
 * internal error) — callers must check this, not assume success.
 */
int compute_hmac_sha256(const uint8_t *data, size_t data_len,
                         const uint8_t *key, size_t key_len,
                         uint8_t out[HMAC_SHA256_LEN]);

/*
 * Verifies a firmware image against an expected HMAC, using constant-
 * time comparison (see .c file for why that matters). Returns 1 if
 * valid, 0 if invalid, -1 on an internal error computing the HMAC.
 */
int secure_boot_verify(const uint8_t *image_data, size_t image_len,
                        const uint8_t *expected_hmac,
                        const uint8_t *key, size_t key_len);

#endif /* SECURE_BOOT_H */