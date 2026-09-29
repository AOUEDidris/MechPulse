#include <iostream>
#include <iomanip>
#include <chrono>
#include <thread>
#include <atomic>
#include <csignal>
#include <cstring>

#ifdef _WIN32
    #define WIN32_LEAN_AND_MEAN
    #define NOMINMAX
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    using socket_t = SOCKET;
    #define INVALID_SOCKET_HANDLE INVALID_SOCKET
    #define CLOSE_SOCKET(s) closesocket(s)
#else
    #include <sys/types.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    using socket_t = int;
    #define INVALID_SOCKET_HANDLE (-1)
    #define CLOSE_SOCKET(s) close(s)
#endif

#include "PacketDef.hpp"
#include "DSPProcessor.hpp"
#include "SignalGenerator.hpp"

namespace mechpulse {

/// @brief Global atomic flag for clean process termination on SIGINT/SIGTERM.
static std::atomic<bool> g_engineRunning{true};

/// @brief Standard POSIX signal handler.
void signalHandler(int signum) {
    (void)signum;
    g_engineRunning = false;
}

#ifdef _WIN32
/// @brief Windows console control event handler.
BOOL WINAPI consoleCtrlHandler(DWORD ctrlType) {
    switch (ctrlType) {
        case CTRL_C_EVENT:
        case CTRL_BREAK_EVENT:
        case CTRL_CLOSE_EVENT:
        case CTRL_SHUTDOWN_EVENT:
            g_engineRunning = false;
            return TRUE;
        default:
            return FALSE;
    }
}
#endif

/// @brief Displays the ASCII art branding banner.
void printBanner() {
    std::cout << R"(
  __  __           _     _____       _           
 |  \/  |         | |   |  __ \     | |          
 | \  / | ___  ___| |__ | |__) |   _| |___  ___  
 | |\/| |/ _ \/ __| '_ \|  ___/ | | | / __|/ _ \ 
 | |  | |  __/ (__| | | | |   | |_| | \__ \  __/ 
 |_|  |_|\___|\___|_| |_|_|    \__,_|_|___/\___| 
          MechPulse Engine v1.0.0
   Industrial Edge DSP & Telemetry Streamer
       Target: 127.0.0.1:9876 (UDP)
)" << std::endl;
}

/// @brief Returns human-readable label for mechanical fault modes.
const char* getFaultName(FaultType fault) {
    switch (fault) {
        case FaultType::Normal:       return "NORMAL (Nominal baseline)";
        case FaultType::Unbalance:    return "UNBALANCE (Dominant 1X peak)";
        case FaultType::Misalignment: return "MISALIGNMENT (Dominant 2X peak)";
        case FaultType::BearingFault: return "BEARING FAULT (BPFO defect impulses)";
        default:                      return "UNKNOWN";
    }
}

} // namespace mechpulse

int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;

    using namespace mechpulse;

    // Register termination signal handlers
    std::signal(SIGINT, signalHandler);
    std::signal(SIGTERM, signalHandler);
#ifdef _WIN32
    SetConsoleCtrlHandler(consoleCtrlHandler, TRUE);
#endif

    printBanner();

    // Initialize Winsock on Windows
#ifdef _WIN32
    WSADATA wsaData;
    int wsaInit = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (wsaInit != 0) {
        std::cerr << "[ERROR] WSAStartup failed with error code: " << wsaInit << std::endl;
        return 1;
    }
    std::cout << "[INIT] Winsock 2.2 successfully initialized." << std::endl;
#endif

    // Create UDP Socket
    socket_t udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (udpSocket == INVALID_SOCKET_HANDLE) {
        std::cerr << "[ERROR] Failed to create UDP socket." << std::endl;
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    // Configure destination address (127.0.0.1:9876)
    sockaddr_in destAddr{};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port   = htons(DEFAULT_UDP_PORT);
#ifdef _WIN32
    destAddr.sin_addr.s_addr = inet_addr("127.0.0.1");
#else
    inet_pton(AF_INET, "127.0.0.1", &destAddr.sin_addr);
#endif

    std::cout << "[INIT] Streaming binary telemetry to 127.0.0.1:" << DEFAULT_UDP_PORT << std::endl;
    std::cout << "[INIT] Packet Size: " << sizeof(VibrationPacket) << " bytes per frame." << std::endl;
    std::cout << "[INIT] Press Ctrl+C to terminate cleanly.\n" << std::endl;

    // Simulation components
    constexpr uint32_t sampleRate = 2560;
    constexpr float runningSpeedHz = 25.0f; // 1500 RPM
    constexpr size_t packetSamples = TIME_DOMAIN_SAMPLES; // 256
    constexpr size_t spectrumBins = FFT_SPECTRUM_BINS;    // 128
    constexpr uint64_t packetsPerFault = 150;            // ~7.5 seconds per fault mode at 20 FPS

    SignalGenerator generator(sampleRate, runningSpeedHz);
    DSPProcessor dsp;

    float rawSignal[packetSamples];
    float windowedSignal[packetSamples];
    float magnitudeSpectrum[spectrumBins];

    const FaultType faultCycle[] = {
        FaultType::Normal,
        FaultType::Unbalance,
        FaultType::Misalignment,
        FaultType::BearingFault
    };
    constexpr size_t numFaultModes = sizeof(faultCycle) / sizeof(faultCycle[0]);

    uint64_t packetCount = 0;
    size_t currentModeIndex = 0;
    generator.setFaultType(faultCycle[currentModeIndex]);

    std::cout << "--------------------------------------------------------------------------------\n"
              << "[FAULT MODE] Initial state: " << getFaultName(faultCycle[currentModeIndex]) << "\n"
              << "--------------------------------------------------------------------------------" << std::endl;

    // Main telemetry loop: 20 FPS (50ms interval)
    while (g_engineRunning) {
        auto frameStartTime = std::chrono::steady_clock::now();

        // Check for periodic fault mode cycling (every 150 packets / 7.5 seconds)
        size_t nextModeIndex = (packetCount / packetsPerFault) % numFaultModes;
        if (nextModeIndex != currentModeIndex) {
            currentModeIndex = nextModeIndex;
            generator.setFaultType(faultCycle[currentModeIndex]);
            std::cout << "\n================================================================================\n"
                      << "[FAULT CYCLE TRANSITION] Switching to: " << getFaultName(faultCycle[currentModeIndex]) << "\n"
                      << "================================================================================" << std::endl;
        }

        // 1. Synthesize time-domain vibration block (256 samples)
        generator.generateBlock(packetSamples, rawSignal);

        // 2. Statistical feature extraction on raw signal
        float rmsVal    = dsp.calculateRMS(rawSignal, packetSamples);
        float peakVal   = dsp.calculatePeak(rawSignal, packetSamples);
        float crestVal  = dsp.calculateCrestFactor(peakVal, rmsVal);
        float kurtVal   = dsp.calculateKurtosis(rawSignal, packetSamples);

        // 3. Spectral processing: Hanning Window -> Radix-2 FFT
        dsp.applyHanningWindow(rawSignal, windowedSignal, packetSamples);
        dsp.computeFFT(windowedSignal, magnitudeSpectrum, packetSamples);

        // 4. Pack binary VibrationPacket struct
        VibrationPacket packet{};
        auto nowEpoch = std::chrono::system_clock::now().time_since_epoch();
        packet.timestamp    = std::chrono::duration<double>(nowEpoch).count();
        packet.rms_velocity = rmsVal;
        packet.peak_accel   = peakVal;
        packet.crest_factor = crestVal;
        packet.kurtosis     = kurtVal;
        packet.sample_rate  = sampleRate;
        packet.sample_count = static_cast<uint32_t>(packetSamples);
        packet.fault_mode   = static_cast<int32_t>(faultCycle[currentModeIndex]);

        std::memcpy(packet.samples, rawSignal, sizeof(rawSignal));
        std::memcpy(packet.fft_spectrum, magnitudeSpectrum, sizeof(magnitudeSpectrum));

        // 5. Send packet via UDP
        int bytesSent = sendto(
            udpSocket,
            reinterpret_cast<const char*>(&packet),
            static_cast<int>(sizeof(packet)),
            0,
            reinterpret_cast<const sockaddr*>(&destAddr),
            sizeof(destAddr)
        );

        if (bytesSent < 0) {
            std::cerr << "[WARNING] sendto() failed to transmit frame #" << packetCount << std::endl;
        }

        // 6. Periodic console status display (approx once per second / 20 packets)
        if (packetCount % 20 == 0) {
            std::cout << std::fixed << std::setprecision(2)
                      << "[STREAMING] Pkt #" << std::setw(6) << packetCount
                      << " | Mode: " << std::setw(1) << packet.fault_mode
                      << " | RMS: " << std::setw(5) << rmsVal << " mm/s"
                      << " | Peak: " << std::setw(5) << peakVal << " g"
                      << " | Crest: " << std::setw(5) << crestVal
                      << " | Kurtosis: " << std::setw(5) << kurtVal
                      << std::endl;
        }

        packetCount++;

        // 7. Precise frame rate regulation: 50ms period (20 FPS)
        auto frameEndTime = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(frameEndTime - frameStartTime);
        auto sleepTime = std::chrono::milliseconds(50) - elapsed;

        if (sleepTime > std::chrono::milliseconds(0)) {
            std::this_thread::sleep_for(sleepTime);
        }
    }

    // Graceful cleanup
    std::cout << "\n[SHUTDOWN] Terminating MechPulse Core Engine..." << std::endl;
    CLOSE_SOCKET(udpSocket);

#ifdef _WIN32
    WSACleanup();
#endif

    std::cout << "[SHUTDOWN] Sockets closed and resources released successfully. Total packets sent: "
              << packetCount << std::endl;

    return 0;
}
