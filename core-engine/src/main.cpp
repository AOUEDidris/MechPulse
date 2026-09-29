#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <cstring>
#include "PacketDef.hpp"
#include "DSPProcessor.hpp"
#include "SignalGenerator.hpp"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
#else
  #include <arpa/inet.h>
  #include <sys/socket.h>
  #include <unistd.h>
#endif

int main(int argc, char* argv[]) {
    std::cout << "=========================================================\n";
    std::cout << "  VibrationGuard Core C++ Engine - Edge DSP Streamer\n";
    std::cout << "  Predictive Maintenance for Algerian Industrial Plants\n";
    std::cout << "=========================================================\n\n";

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "[-] Error initializing Winsock.\n";
        return 1;
    }
#endif

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        std::cerr << "[-] Failed to create UDP socket.\n";
        return 1;
    }

    sockaddr_in destAddr{};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(9876);
    destAddr.sin_addr.s_addr = inet_addr("127.0.0.1");

    std::cout << "[+] Streaming real-time vibration data to 127.0.0.1:9876...\n";
    std::cout << "[+] Packet size: " << sizeof(VibrationPacket) << " bytes\n";
    std::cout << "[+] Cycle: Normal -> Unbalance -> Misalignment -> Bearing Defect\n\n";

    const uint32_t SAMPLE_RATE = 1000; // 1000 Hz
    const size_t BLOCK_SIZE = 256;      // 256 samples per block

    SignalGenerator generator(SAMPLE_RATE, 25.0f); // 25 Hz = 1500 RPM
    DSPProcessor dsp;

    std::vector<float> raw_signal;
    std::vector<float> windowed_signal;
    std::vector<float> spectrum;

    int cycle_counter = 0;
    FaultType current_type = FaultType::NORMAL;

    while (true) {
        // تغيير الحالة تلقائياً كل 150 حزمة (حوالي 7.5 ثوانٍ لكل حالة لإظهار القدرات)
        cycle_counter++;
        if (cycle_counter % 150 == 0) {
            int next_fault = (static_cast<int>(current_type) + 1) % 4;
            current_type = static_cast<FaultType>(next_fault);
            generator.setFaultType(current_type);

            std::cout << "[Fault Simulation Switched] -> ";
            switch (current_type) {
                case FaultType::NORMAL: std::cout << "NORMAL (Healthy ISO Zone A)\n"; break;
                case FaultType::UNBALANCE: std::cout << "UNBALANCE (1X Dominant)\n"; break;
                case FaultType::MISALIGNMENT: std::cout << "MISALIGNMENT (1X + 2X Dominant)\n"; break;
                case FaultType::BEARING_FAULT: std::cout << "BEARING DEFECT (BPFO Impacts)\n"; break;
            }
        }

        // 1. توليد الإشارة اللحظية
        generator.generateBlock(BLOCK_SIZE, raw_signal);

        // 2. معالجة الإشارة في C++ (Windowing + FFT)
        dsp.applyHanningWindow(raw_signal, windowed_signal);
        dsp.computeFFT(windowed_signal, spectrum);

        // 3. استخراج المؤشرات الإحصائية
        float rms = dsp.calculateRMS(raw_signal);
        float peak = dsp.calculatePeak(raw_signal);
        float crest = dsp.calculateCrestFactor(peak, rms);
        float kurtosis = dsp.calculateKurtosis(raw_signal);

        // 4. تعبئة الحزمة الثنائية
        VibrationPacket packet{};
        packet.timestamp = std::chrono::duration<double>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        packet.rms_velocity = rms;
        packet.peak_accel = peak;
        packet.crest_factor = crest;
        packet.kurtosis = kurtosis;
        packet.sample_rate = SAMPLE_RATE;
        packet.sample_count = static_cast<uint32_t>(BLOCK_SIZE);
        packet.fault_mode = static_cast<int32_t>(current_type);

        for (size_t i = 0; i < BLOCK_SIZE && i < 256; ++i) {
            packet.samples[i] = raw_signal[i];
        }
        for (size_t i = 0; i < spectrum.size() && i < 128; ++i) {
            packet.fft_spectrum[i] = spectrum[i];
        }

        // 5. الإرسال عبر UDP
        sendto(sock, reinterpret_cast<const char*>(&packet), sizeof(packet), 0,
               reinterpret_cast<sockaddr*>(&destAddr), sizeof(destAddr));

        // معدل إرسال 20 إطاراً في الثانية (50ms)
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

#ifdef _WIN32
    closesocket(sock);
    WSACleanup();
#else
    close(sock);
#endif

    return 0;
}
