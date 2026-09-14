CC = gcc
CFLAGS = -Wall -Wextra -std=gnu11 -g

.PHONY: all clean test setup-vcan

all: sil_harness

sil_harness: src/main_sil.c src/pid_decode.c hal/can_hal_socketcan.c
	$(CC) $(CFLAGS) -o $@ $^

test: tests/test_pid_decode.c src/pid_decode.c
	$(CC) $(CFLAGS) -o test_runner $^ -lm
	./test_runner

setup-vcan:
	sudo modprobe vcan
	sudo ip link add dev vcan0 type vcan || true
	sudo ip link set up vcan0

clean:
	rm -f sil_harness test_runner