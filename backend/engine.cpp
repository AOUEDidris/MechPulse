/*
 * ============================================================================
 *  MechPulse — Industrial Vibration Monitoring Engine
 *  Real-Time Edge DSP & UDP Streaming Server
 * ============================================================================
 *
 *  This C++ engine simulates realistic mechanical vibration signals for
 *  rotating machinery (pumps, turbines, compressors, electric motors),
 *  performs real-time digital signal processing (Hanning Window + FFT),
 *  and streams binary packets to the Python frontend via UDP at 20 FPS.
 *
 *  Simulated Fault Types:
 *    0 = Normal Operation     (ISO Zone A/B — healthy machine)
 *    1 = Unbalance            (dominant 1X frequency at shaft speed)
 *    2 = Misalignment         (dominant 2X + 3X harmonics)
 *    3 = Bearing Defect       (BPFO impulse train at 4.8x shaft speed)
 *
 *  Build Instructions (Windows):
 *    mkdir build && cd build
 *    cmake .. && cmake --build . --config Release
 *    ./MechPulseEngine
 *
 *  Build Instructions (Linux/macOS):
 *    mkdir build && cd build && cmake .. && make
 *    ./MechPulseEngine
 *
 *  Protocol: UDP Binary Packed Struct (1572 bytes per packet)
 *  Target:   127.0.0.1:9876
 *
 *  Author:  MechPulse Team
 *  License: MIT
 * ============================================================================
 */

#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <thread>
#include <csignal>

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef int socklen_t;
#else
  #include <arpa/inet.h>
  #include <sys/socket.h>
  #include <unistd.h>
  #define closesocket close
  #define SOCKET int
  #define INVALID_SOCKET -1
#endif

#ifndef M_PI
  #define M_PI 3.14159265358979323846
#endif

// ============================================================================
//  SECTION 1: Binary Packet Definition (shared with Python frontend)
// ============================================================================

#pragma pack(push, 1)
struct VibrationPacket {
    double   timestamp;         // Unix timestamp (seconds)
    float    rms_velocity;      // RMS vibration velocity (mm/s) — ISO 10816
    float    peak_accel;        // Peak acceleration (g)
    float    crest_factor;      // Crest Factor = Peak / RMS (bearing health)
    float    kurtosis;          // Kurtosis (impulse/shock detection)
    uint32_t sample_rate;       // Sampling rate in Hz (e.g., 1000)
    uint32_t sample_count;      // Samples per block (256)
    int32_t  fault_mode;        // 0=Normal, 1=Unbalance, 2=Misalignment, 3=Bearing
    float    samples[256];      // Time-domain waveform buffer
    float    fft_spectrum[128]; // Single-sided FFT magnitude spectrum
};
#pragma pack(pop)

static_assert(sizeof(VibrationPacket) == 1572, "Packet size must match Python struct");

// ============================================================================
//  SECTION 2: DSP Processor — Hanning Window + Cooley-Tukey FFT + Statistics
// ============================================================================

class DSPProcessor {
public:
    // Apply Hanning window to reduce spectral leakage in FFT
    static void applyHanningWindow(const std::vector<float>& in, std::vector<float>& out) {
        size_t N = in.size();
        out.resize(N);
        for (size_t i = 0; i < N; ++i) {
            float w = 0.5f * (1.0f - cosf(2.0f * (float)M_PI * (float)i / (float)(N - 1)));
            out[i] = in[i] * w;
        }
    }

    // Compute single-sided FFT magnitude spectrum (Radix-2 Cooley-Tukey)
    static void computeFFT(const std::vector<float>& signal, std::vector<float>& spectrum) {
        size_t N = signal.size();
        std::vector<std::complex<float>> data(N);
        for (size_t i = 0; i < N; ++i)
            data[i] = std::complex<float>(signal[i], 0.0f);

        fftRecursive(data);

        size_t half = N / 2;
        spectrum.resize(half);
        for (size_t i = 0; i < half; ++i)
            spectrum[i] = std::abs(data[i]) * 2.0f / (float)N;
    }

    // RMS (Root Mean Square) — ISO 10816 primary metric
    static float calculateRMS(const std::vector<float>& s) {
        float sum = 0.0f;
        for (float v : s) sum += v * v;
        return sqrtf(sum / (float)s.size());
    }

    // Peak absolute value
    static float calculatePeak(const std::vector<float>& s) {
        float mx = 0.0f;
        for (float v : s) { float a = fabsf(v); if (a > mx) mx = a; }
        return mx;
    }

    // Crest Factor = Peak / RMS (elevated in bearing faults)
    static float calculateCrestFactor(float peak, float rms) {
        return (rms > 1e-4f) ? (peak / rms) : 0.0f;
    }

    // Kurtosis — measures impulsiveness (>4.5 indicates bearing damage)
    static float calculateKurtosis(const std::vector<float>& s) {
        if (s.size() < 4) return 3.0f;
        float mean = 0.0f;
        for (float v : s) mean += v;
        mean /= (float)s.size();

        float m2 = 0.0f, m4 = 0.0f;
        for (float v : s) {
            float d = v - mean;
            float d2 = d * d;
            m2 += d2;
            m4 += d2 * d2;
        }
        float var = m2 / (float)s.size();
        if (var < 1e-6f) return 3.0f;
        return (m4 / (float)s.size()) / (var * var);
    }

private:
    static void fftRecursive(std::vector<std::complex<float>>& a) {
        size_t n = a.size();
        if (n <= 1) return;
        std::vector<std::complex<float>> even(n / 2), odd(n / 2);
        for (size_t i = 0; i < n / 2; i++) {
            even[i] = a[2 * i];
            odd[i]  = a[2 * i + 1];
        }
        fftRecursive(even);
        fftRecursive(odd);
        float ang = 2.0f * (float)M_PI / (float)n;
        std::complex<float> w(1.0f, 0.0f), wn(cosf(ang), -sinf(ang));
        for (size_t i = 0; i < n / 2; i++) {
            a[i]         = even[i] + w * odd[i];
            a[i + n / 2] = even[i] - w * odd[i];
            w *= wn;
        }
    }
};

// ============================================================================
//  SECTION 3: Mechanical Signal Generator — Realistic Fault Simulation
// ============================================================================

enum class FaultType : int32_t {
    Normal       = 0,  // Healthy machine (ISO Zone A/B)
    Unbalance    = 1,  // Mass unbalance on rotor (strong 1X)
    Misalignment = 2,  // Shaft/coupling misalignment (strong 2X + 3X)
    BearingFault = 3   // Bearing outer race defect (BPFO impulses)
};

class SignalGenerator {
public:
    SignalGenerator(uint32_t rate = 1000, float speed_hz = 25.0f)
        : m_rate(rate), m_speed(speed_hz), m_time(0.0f), m_fault(FaultType::Normal),
          m_has_spare(false), m_spare(0.0f) {}

    void setFault(FaultType f) { m_fault = f; }
    FaultType getFault() const { return m_fault; }

    void generate(size_t count, std::vector<float>& buf) {
        buf.resize(count);
        float dt = 1.0f / (float)m_rate;
        float f1 = m_speed;            // 1X = 25 Hz (1500 RPM)
        float f2 = 2.0f * m_speed;     // 2X = 50 Hz
        float f3 = 3.0f * m_speed;     // 3X = 75 Hz
        float f_bpfo = 4.8f * m_speed; // BPFO ~ 120 Hz

        for (size_t i = 0; i < count; ++i) {
            float sig = 0.0f;
            float noise = gaussian(0.25f);
            float t = m_time;

            switch (m_fault) {
                case FaultType::Normal:
                    sig = 0.8f * sinf(2.0f*(float)M_PI*f1*t) + noise;
                    break;

                case FaultType::Unbalance:
                    sig = 4.8f * sinf(2.0f*(float)M_PI*f1*t)
                        + 0.4f * sinf(2.0f*(float)M_PI*f2*t) + noise;
                    break;

                case FaultType::Misalignment:
                    sig = 2.5f * sinf(2.0f*(float)M_PI*f1*t)
                        + 4.2f * sinf(2.0f*(float)M_PI*f2*t)
                        + 1.2f * sinf(2.0f*(float)M_PI*f3*t) + noise;
                    break;

                case FaultType::BearingFault: {
                    float mod = sinf(2.0f*(float)M_PI*f_bpfo*t);
                    float pulse = (mod > 0.85f) ? 7.5f * (mod - 0.85f) : 0.0f;
                    sig = 1.2f * sinf(2.0f*(float)M_PI*f1*t) + pulse + gaussian(0.5f);
                    break;
                }
            }

            buf[i] = sig;
            m_time += dt;
            if (m_time > 1000.0f) m_time = 0.0f;
        }
    }

private:
    uint32_t  m_rate;
    float     m_speed;
    float     m_time;
    FaultType m_fault;
    bool      m_has_spare;
    float     m_spare;

    // Box-Muller Gaussian noise generator
    float gaussian(float stddev) {
        if (m_has_spare) { m_has_spare = false; return m_spare * stddev; }
        float u, v, s;
        do {
            u = 2.0f * ((float)rand() / RAND_MAX) - 1.0f;
            v = 2.0f * ((float)rand() / RAND_MAX) - 1.0f;
            s = u * u + v * v;
        } while (s >= 1.0f || s == 0.0f);
        s = sqrtf(-2.0f * logf(s) / s);
        m_spare = v * s;
        m_has_spare = true;
        return u * s * stddev;
    }
};

// ============================================================================
//  SECTION 4: Main — UDP Streaming Loop
// ============================================================================

static volatile bool g_running = true;

void signalHandler(int) { g_running = false; }

int main() {
    std::signal(SIGINT, signalHandler);

    // --- ASCII Banner ---
    std::cout << R"(
    ___  ___          _     ______      _
    |  \/  |         | |    | ___ \    | |
    | .  . | ___  ___| |__  | |_/ /   _| |___  ___
    | |\/| |/ _ \/ __| '_ \ |  __/ | | | / __|/ _ \
    | |  | |  __/ (__| | | || |  | |_| | \__ \  __/
    \_|  |_/\___|\___|_| |_|\_|   \__,_|_|___/\___|
    )" << std::endl;
    std::cout << "  Real-Time Vibration DSP Engine v1.0.0\n";
    std::cout << "  ISO 10816-3 Compliant | Industry 4.0\n";
    std::cout << "  ==========================================\n\n";

    // --- Initialize Network ---
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        std::cerr << "[-] Winsock init failed.\n"; return 1;
    }
#endif

    SOCKET sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "[-] Socket creation failed.\n"; return 1;
    }

    sockaddr_in dest{};
    dest.sin_family = AF_INET;
    dest.sin_port = htons(9876);
    dest.sin_addr.s_addr = inet_addr("127.0.0.1");

    std::cout << "[+] Streaming vibration data to 127.0.0.1:9876 (20 FPS)\n";
    std::cout << "[+] Packet size: " << sizeof(VibrationPacket) << " bytes\n";
    std::cout << "[+] Cycle: Normal -> Unbalance -> Misalignment -> Bearing\n\n";

    // --- DSP Processing Loop ---
    const uint32_t RATE = 1000;
    const size_t   BLOCK = 256;

    SignalGenerator gen(RATE, 25.0f);
    std::vector<float> raw, windowed, spectrum;

    int counter = 0;
    FaultType current = FaultType::Normal;

    while (g_running) {
        counter++;

        // Auto-cycle fault mode every ~7.5 seconds (150 packets)
        if (counter % 150 == 0) {
            int next = (static_cast<int>(current) + 1) % 4;
            current = static_cast<FaultType>(next);
            gen.setFault(current);
            const char* names[] = {"NORMAL (Healthy)", "UNBALANCE (1X)",
                                   "MISALIGNMENT (2X)", "BEARING DEFECT (BPFO)"};
            std::cout << "[Mode Switch] -> " << names[next] << std::endl;
        }

        // 1. Generate signal block
        gen.generate(BLOCK, raw);

        // 2. DSP: Window + FFT + Statistics
        DSPProcessor::applyHanningWindow(raw, windowed);
        DSPProcessor::computeFFT(windowed, spectrum);

        float rms   = DSPProcessor::calculateRMS(raw);
        float peak  = DSPProcessor::calculatePeak(raw);
        float crest = DSPProcessor::calculateCrestFactor(peak, rms);
        float kurt  = DSPProcessor::calculateKurtosis(raw);

        // 3. Pack binary packet
        VibrationPacket pkt{};
        pkt.timestamp = std::chrono::duration<double>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        pkt.rms_velocity  = rms;
        pkt.peak_accel    = peak;
        pkt.crest_factor  = crest;
        pkt.kurtosis      = kurt;
        pkt.sample_rate   = RATE;
        pkt.sample_count  = (uint32_t)BLOCK;
        pkt.fault_mode    = static_cast<int32_t>(current);

        for (size_t i = 0; i < BLOCK; ++i) pkt.samples[i] = raw[i];
        for (size_t i = 0; i < spectrum.size() && i < 128; ++i)
            pkt.fft_spectrum[i] = spectrum[i];

        // 4. Send via UDP
        sendto(sock, reinterpret_cast<const char*>(&pkt), sizeof(pkt), 0,
               reinterpret_cast<sockaddr*>(&dest), sizeof(dest));

        std::this_thread::sleep_for(std::chrono::milliseconds(50)); // 20 FPS
    }

    // --- Cleanup ---
    std::cout << "\n[+] Engine stopped gracefully.\n";
    closesocket(sock);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
