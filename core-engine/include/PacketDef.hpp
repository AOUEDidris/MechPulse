#pragma once

#ifndef MECHPULSE_PACKET_DEF_HPP
#define MECHPULSE_PACKET_DEF_HPP

#include <cstdint>
#include <cstddef>

namespace mechpulse {

/// @brief Default telemetry configuration constants
constexpr size_t TIME_DOMAIN_SAMPLES = 256;
constexpr size_t FFT_SPECTRUM_BINS   = 128;
constexpr uint16_t DEFAULT_UDP_PORT  = 9876;

#pragma pack(push, 1)
/// @brief Binary packed structure for real-time UDP vibration telemetry between C++ core engine and Python UI.
/// Total packet size is strictly 1572 bytes to align across heterogeneous platforms.
struct VibrationPacket {
    double   timestamp;         // Unix timestamp (seconds)
    float    rms_velocity;      // RMS velocity (mm/s) per ISO 10816
    float    peak_accel;        // Peak acceleration (g)
    float    crest_factor;      // Crest Factor = Peak / RMS
    float    kurtosis;          // Kurtosis (bearing health indicator)
    uint32_t sample_rate;       // Sampling rate in Hz
    uint32_t sample_count;      // Number of time-domain samples (256)
    int32_t  fault_mode;        // 0=Normal, 1=Unbalance, 2=Misalignment, 3=BearingFault
    float    samples[256];      // Time-domain waveform
    float    fft_spectrum[128]; // FFT magnitude spectrum
};
#pragma pack(pop)

static_assert(sizeof(VibrationPacket) == 1572, "Packet size mismatch with Python receiver");

} // namespace mechpulse

#endif // MECHPULSE_PACKET_DEF_HPP
