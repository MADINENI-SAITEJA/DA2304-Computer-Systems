load Multiplier.hdl,
output-file Multiplier.out,
compare-to Multiplier.cmp,
output-list a%B1.16.1 b%B1.16.1 low%B1.16.1 high%B1.16.1;

// Test 1: Zero (0 * 0)
set a %B0000000000000000,
set b %B0000000000000000,
eval,
output;

// Test 2: Basic identity (1 * 1)
set a %B0000000000000001,
set b %B0000000000000001,
eval,
output;

// Test 3: Small numbers (5 * 6)
set a %B0000000000000101,
set b %B0000000000000110,
eval,
output;

// Test 4: 256 * 256 = 65536
set a %B0000000100000000,
set b %B0000000100000000,
eval,
output;

// Test 5: Maximum positive 16-bit values (32767 * 32767)
set a %B0111111111111111,
set b %B0111111111111111,
eval,
output;

// Test 6: All 1s (-1 * -1)
set a %B1111111111111111,
set b %B1111111111111111,
eval,
output;